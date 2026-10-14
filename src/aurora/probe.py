"""Prova manual isolada; não implementa as garantias da API de produção."""

import argparse
import asyncio
import json
import os

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.apps import App, ResumabilityConfig
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import ToolContext
from google.genai import types

from aurora.config import Settings

APP_NAME = "aurora_probe"
USER_ID = "morador_101"


def effect(action: str, details: dict, ctx: ToolContext) -> dict:
    if ctx.tool_confirmation is None:
        ctx.request_confirmation(
            hint="Aprovar pela confirmação estruturada.", payload=details
        )
        return {"status": "pendente"}
    if not ctx.tool_confirmation.confirmed:
        return {"status": "negada"}
    key = f"efeito:{ctx.function_call_id}"
    result = {"status": "executada", "acao": action, "detalhes": details}
    ctx.state[key] = result
    return result


def reservar(area: str, data: str, tool_context: ToolContext) -> dict:
    """Solicita uma reserva de demonstração com confirmação, sem alterar dados reais."""
    return effect("reservar", {"area": area, "data": data}, tool_context)


def autorizar(nome: str, data: str, tool_context: ToolContext) -> dict:
    """Solicita uma visita de demonstração com confirmação, sem alterar dados reais."""
    return effect("autorizar", {"nome": nome, "data": data}, tool_context)


def build_app(model: str) -> App:
    def llm():
        return Gemini(model=model, retry_options=types.HttpRetryOptions(attempts=1))

    config = types.GenerateContentConfig(max_output_tokens=512)
    common = (
        "Responda em português. Execute pedidos usando sua tool. "
        "Nunca invente resultados. Para outro assunto, transfira ao principal. "
        "Após resultado pendente, aguarde a confirmação estruturada."
    )
    root = Agent(
        name="principal",
        model=llm(),
        generate_content_config=config,
        instruction="Transfira reservas para reservas e visitas para visitantes.",
        sub_agents=[
            Agent(
                name="reservas",
                model=llm(),
                generate_content_config=config,
                description="Reservas de áreas",
                instruction=common,
                tools=[reservar],
            ),
            Agent(
                name="visitantes",
                model=llm(),
                generate_content_config=config,
                description="Autorizações de visitas",
                instruction=common,
                tools=[autorizar],
            ),
        ],
    )
    return App(
        name=APP_NAME,
        root_agent=root,
        resumability_config=ResumabilityConfig(is_resumable=True),
    )


def pending(session) -> list[dict]:
    answered = {
        response.id
        for event in session.events
        for response in event.get_function_responses()
        if response.name == "adk_request_confirmation"
    }
    return [
        {
            "id": call.id,
            "session_id": session.id,
            "invocation_id": event.invocation_id,
            "agente": event.author,
            "original": call.args["originalFunctionCall"],
        }
        for event in session.events
        for call in event.get_function_calls()
        if call.name == "adk_request_confirmation" and call.id not in answered
    ]


async def run(args) -> None:
    settings = Settings.from_env()
    if args.command in {"mensagem", "confirmar"} and not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit(
            "Configure GOOGLE_API_KEY no .env local antes da prova com Gemini."
        )
    folder = settings.data_dir / "prova"
    folder.mkdir(parents=True, exist_ok=True)
    service = DatabaseSessionService(
        db_url=f"sqlite+aiosqlite:///{folder / 'sessoes.sqlite3'}"
    )
    try:
        if args.command == "criar":
            session = await service.create_session(
                app_name=APP_NAME, user_id=USER_ID, state={"apartamento": "101"}
            )
            print(session.id)
            return
        loaded_session = await service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=args.session
        )
        if loaded_session is None:
            raise SystemExit("Sessão inexistente.")
        session = loaded_session
        if args.command == "eventos":
            print(
                json.dumps(
                    [
                        e.model_dump(mode="json", exclude_none=True)
                        for e in session.events
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        if args.command == "estado":
            print(
                json.dumps(
                    {"state": session.state, "pendencias": pending(session)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        invocation_id = None
        if args.command == "mensagem":
            if pending(session):
                raise SystemExit(
                    "Responda às pendências antes de enviar outra mensagem."
                )
            message = types.Content(role="user", parts=[types.Part(text=args.texto)])
        else:
            item = next((p for p in pending(session) if p["id"] == args.id), None)
            if item is None:
                raise SystemExit("Confirmação não pendente nesta sessão.")
            invocation_id = item["invocation_id"]
            message = types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            id=item["id"],
                            name="adk_request_confirmation",
                            response={"confirmed": args.decisao == "sim"},
                        )
                    )
                ],
            )
        runner = Runner(app=build_app(settings.model), session_service=service)
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            invocation_id=invocation_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=5),
        ):
            print(event.model_dump_json(exclude_none=True))
        loaded_session = await service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session.id
        )
        if loaded_session is None:
            raise RuntimeError("Sessão desapareceu durante a execução.")
        session = loaded_session
        print(
            json.dumps(
                {"state": session.state, "pendencias": pending(session)},
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        await service.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("criar")
    for command in ("eventos", "estado", "mensagem", "confirmar"):
        sub = commands.add_parser(command)
        sub.add_argument("session")
        if command == "mensagem":
            sub.add_argument("texto")
        elif command == "confirmar":
            sub.add_argument("id")
            sub.add_argument("decisao", choices=["sim", "nao"])
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
