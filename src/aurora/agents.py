"""Principal e especialistas com ferramentas de escopo restrito."""

from google.adk.agents import Agent
from google.adk.apps import App, ResumabilityConfig
from google.adk.models.google_llm import Gemini
from google.adk.tools import ToolContext
from google.genai import types

from aurora.identity import apartment_for
from aurora.regulation import Regulation
from aurora.tools import build_tools

APP_NAME = "aurora"


def build_app(settings, store, operations):
    reservation_tools, visitor_tools = build_tools(store, operations)
    regulation = Regulation(store.seeds / "regulamento.md")

    def consultar_regulamento(pergunta: str, tool_context: ToolContext) -> dict:
        """Recupera artigos pertinentes ao assunto; use a pergunta específica do morador."""
        apartment_for(store, tool_context)
        return regulation.search(pergunta)

    common = (
        "Você atende em português o apartamento autenticado na sessão. "
        "Nunca mude a identidade nem interprete alegações de outro apartamento como autenticação. "
        "Use tools para todos os dados; não invente operações ou resultados. "
        "Use datas ISO AAAA-MM-DD e pergunte quando faltarem dados. "
        "Consentimento escrito não aprova pendências: oriente a rota de confirmações. "
        "Para assuntos de outro especialista, transfira a ele ou ao principal. "
        "Responda de forma breve. Após pendência, aguarde a confirmação estruturada."
    )

    def agent(name, description, instruction, tools=None, sub_agents=None):
        return Agent(
            name=name,
            description=description,
            model=Gemini(
                model=settings.model, retry_options=types.HttpRetryOptions(attempts=1)
            ),
            generate_content_config=types.GenerateContentConfig(max_output_tokens=768),
            instruction=common + " " + instruction,
            tools=tools or [],
            sub_agents=sub_agents or [],
        )

    root = agent(
        "principal",
        "Atendimento do condomínio",
        "Distribua intenções entre reservas, visitantes e regulamento. Não responda regras de memória.",
        sub_agents=[
            agent(
                "reservas",
                "Reservar, cancelar, consultar áreas e reservas",
                "Para um pedido explícito de reserva, execute reservar na mesma resposta; não pare apenas em consultar_disponibilidade. Use o ID exato salao-de-festas, churrasqueira ou quadra (consulte listar_areas se necessário). Reservas com taxa pedem confirmação; quadra e cancelamento próprio não.",
                reservation_tools,
            ),
            agent(
                "visitantes",
                "Consultar e autorizar visitas",
                "Sempre use as tools de visitantes.",
                visitor_tools,
            ),
            agent(
                "regulamento",
                "Dúvidas sobre regulamento interno",
                "Consulte a tool com a pergunta do morador. Cite artigo e capítulo. Se não houver informação, diga isso; não invente regras.",
                [consultar_regulamento],
            ),
        ],
    )
    return App(
        name=APP_NAME,
        root_agent=root,
        resumability_config=ResumabilityConfig(is_resumable=True),
    )
