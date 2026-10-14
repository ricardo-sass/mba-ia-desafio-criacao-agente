"""Tools com identidade confiável e argumentos validados."""

import re
from datetime import date

from google.adk.tools import ToolContext

from aurora.identity import apartment_for
from aurora.repositories import Operations
from aurora.storage import Storage


def valid_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Use uma data no formato AAAA-MM-DD.")
    return date.fromisoformat(value).isoformat()


def build_tools(store: Storage, operations: Operations):
    def area_args(area, data):
        item = store.area(area)
        if not item:
            raise ValueError("Área desconhecida; consulte listar_areas.")
        return {
            "area": area,
            "data": valid_date(data),
            "taxa_centavos": item["taxa_centavos"],
        }

    def perform(action, args, ctx, requires_confirmation):
        apartment = apartment_for(store, ctx)
        if requires_confirmation:
            row = operations.prepare(
                ctx.session.id,
                ctx.invocation_id,
                ctx.agent_name,
                ctx.function_call_id,
                action,
                args,
            )
            if ctx.tool_confirmation is None:
                if row["status"] != "pendente":
                    raise ValueError("Retomada exige confirmação estruturada original.")
                ctx.request_confirmation(
                    hint="Responda pela rota de confirmações.", payload=args
                )
                return {"status": "pendente", "detalhes": args}
        return operations.execute(
            ctx.session.id,
            apartment,
            ctx.invocation_id,
            ctx.agent_name,
            ctx.function_call_id,
            action,
            args,
            ctx.tool_confirmation if requires_confirmation else None,
        )

    def listar_areas(tool_context: ToolContext) -> dict:
        """Lista IDs das áreas e taxas em centavos."""
        apartment_for(store, tool_context)
        return {"areas": store.areas()}

    def consultar_disponibilidade(
        area: str, data: str, tool_context: ToolContext
    ) -> dict:
        """Informa apenas livre/ocupada para uma área e data ISO; não identifica ocupantes."""
        apartment_for(store, tool_context)
        try:
            args = area_args(area, data)
        except ValueError as exc:
            return {"erro": str(exc)}
        return {
            "area": area,
            "data": args["data"],
            "disponivel": store.available(area, args["data"]),
        }

    def minhas_reservas(tool_context: ToolContext) -> dict:
        """Consulta exclusivamente reservas ativas do apartamento autenticado."""
        return {"reservas": store.reservations(apartment_for(store, tool_context))}

    def reservar(area: str, data: str, tool_context: ToolContext) -> dict:
        """Reserva área pelo ID e data ISO; taxas exigem confirmação pela API."""
        try:
            args = area_args(area, data)
        except ValueError as exc:
            return {"erro": str(exc)}
        return perform("reservar", args, tool_context, args["taxa_centavos"] > 0)

    def cancelar(
        codigo: str = "",
        area: str = "",
        data: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Cancela reserva própria por código OU área/data; não exige confirmação."""
        if codigo:
            args = {"codigo": codigo}
        else:
            try:
                values = area_args(area, data)
            except ValueError as exc:
                return {"erro": str(exc)}
            args = {"area": area, "data": values["data"]}
        return perform("cancelar", args, tool_context, False)

    def meus_visitantes(tool_context: ToolContext) -> dict:
        """Lista somente visitantes do apartamento autenticado."""
        return {"visitantes": store.visitors(apartment_for(store, tool_context))}

    def autorizar(nome: str, data: str, tool_context: ToolContext) -> dict:
        """Solicita autorização de visitante; sempre exige confirmação pela API."""
        try:
            day = valid_date(data)
            name = " ".join(nome.split())
            if not name or len(name) > 200:
                raise ValueError("Informe um nome entre 1 e 200 caracteres.")
        except ValueError as exc:
            return {"erro": str(exc)}
        return perform("autorizar", {"nome": name, "data": day}, tool_context, True)

    return [
        listar_areas,
        consultar_disponibilidade,
        minhas_reservas,
        reservar,
        cancelar,
    ], [meus_visitantes, autorizar]
