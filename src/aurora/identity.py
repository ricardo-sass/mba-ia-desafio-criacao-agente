"""Identidade resolvida antes de qualquer consulta pessoal."""

from google.adk.tools import ToolContext

from aurora.storage import Storage


def apartment_for(store: Storage, context: ToolContext) -> str:
    binding = store.binding(context.session.id)
    if (
        not binding
        or binding["adk_user_id"] != context.session.user_id
        or binding["apartamento"] != context.state.get("apartamento")
    ):
        raise ValueError("Identidade de sessão inválida")
    return binding["apartamento"]
