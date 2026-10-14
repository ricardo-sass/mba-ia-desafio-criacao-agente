"""Runner persistente, serialização por sessão e retomada de decisões duráveis."""

import asyncio
import json
from contextlib import asynccontextmanager
from uuid import uuid4

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from aurora.agents import APP_NAME, build_app
from aurora.repositories import Operations
from aurora.storage import Storage


class Runtime:
    def __init__(self, settings):
        self.store = Storage(settings.data_dir)
        self.operations = Operations(self.store)
        self.sessions = DatabaseSessionService(
            db_url=f"sqlite+aiosqlite:///{settings.data_dir / 'sessoes.sqlite3'}"
        )
        self.runner = Runner(
            app=build_app(settings, self.store, self.operations),
            session_service=self.sessions,
        )
        self.locks = {}

    @asynccontextmanager
    async def locked(self, session):
        # Refcount evita reter locks indefinidamente, inclusive em IDs inexistentes.
        entry = self.locks.setdefault(session, [asyncio.Lock(), 0])
        entry[1] += 1
        try:
            async with entry[0]:
                yield
        finally:
            entry[1] -= 1
            if not entry[1]:
                self.locks.pop(session, None)

    async def create_session(self, apartment):
        if not self.store.apartment(apartment):
            raise KeyError("Apartamento inexistente")
        session_id = str(uuid4())
        user_id = f"apartamento_{apartment}"
        await self.sessions.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            state={"apartamento": apartment},
        )
        self.store.bind(session_id, apartment, user_id)
        return session_id

    async def session(self, session_id):
        binding = self.store.binding(session_id)
        if not binding:
            raise KeyError("Sessão inexistente")
        session = await self.sessions.get_session(
            app_name=APP_NAME, user_id=binding["adk_user_id"], session_id=session_id
        )
        if session is None:
            raise KeyError("Sessão inexistente")
        return session

    def correlate(self, session_id, event):
        for call in event.get_function_calls():
            if call.name == "adk_request_confirmation":
                self.operations.correlate(
                    session_id,
                    event.invocation_id,
                    event.author,
                    call.args["originalFunctionCall"],
                    call.id,
                )

    async def reconcile(self, session_id):
        session = await self.session(session_id)
        for event in session.events:
            self.correlate(session_id, event)
        for row in self.operations.unresolved(session_id):
            await self.resume(session_id, row)

    async def run(self, session_id, message, invocation=None):
        session = await self.session(session_id)
        texts: list[str] = []
        async for event in self.runner.run_async(
            user_id=session.user_id,
            session_id=session_id,
            invocation_id=invocation,
            new_message=message,
            run_config=RunConfig(max_llm_calls=8),
        ):
            self.correlate(session_id, event)
            if event.error_code:
                raise RuntimeError("Falha na execução do modelo")
            if event.is_final_response() and event.content:
                texts.extend(
                    p.text
                    for p in event.content.parts or []
                    if p.text and not p.thought
                )
        return "\n".join(texts)

    async def resume(self, session_id, row):
        message = types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        name="adk_request_confirmation",
                        id=row["confirmation_call_id"],
                        response={"confirmed": bool(row["decisao"])},
                    )
                )
            ],
        )
        try:
            await self.run(session_id, message, row["invocation_id"])
        except Exception:
            # Se o efeito foi gravado e só a redação final falhou, o resultado ainda é definitivo.
            latest = self.operations.get(row["id"])
            if latest["resultado_json"] is None:
                raise
        latest = self.operations.get(row["id"])
        if latest["resultado_json"] is None:
            raise RuntimeError("Decisão registrada; retomada ainda não concluída")
        return json.loads(latest["resultado_json"])

    def envelope(self, session_id, text):
        return {
            "resposta": text,
            "confirmacoes_pendentes": self.operations.pending(session_id),
        }

    async def message(self, session_id, text):
        async with self.locked(session_id):
            await self.reconcile(session_id)
            if self.operations.pending(session_id):
                return self.envelope(
                    session_id,
                    "Responda às confirmações pendentes pela rota de confirmações.",
                )
            result = await self.run(
                session_id, types.Content(role="user", parts=[types.Part(text=text)])
            )
            return self.envelope(session_id, result)

    async def confirm(self, session_id, public_id, decision):
        async with self.locked(session_id):
            await self.session(session_id)
            # ID inválido é rejeitado antes de qualquer retomada.
            row = self.operations.decide(session_id, public_id, decision)
            result = await self.resume(session_id, row)
            return self.envelope(session_id, json.dumps(result, ensure_ascii=False))

    async def events(self, session_id):
        async with self.locked(session_id):
            session = await self.session(session_id)
            return [
                e.model_dump(mode="json", exclude_none=True) for e in session.events
            ]

    async def close(self):
        await self.runner.close()
        await self.sessions.close()
