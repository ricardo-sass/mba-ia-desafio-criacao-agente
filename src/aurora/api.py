"""Contrato HTTP do assistente Aurora."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from google.genai.errors import APIError

from aurora.config import Settings
from aurora.repositories import Conflict
from aurora.runtime import Runtime
from aurora.schemas import ConfirmationInput, MessageInput, SessionInput


def create_app():
    @asynccontextmanager
    async def lifespan(app):
        app.state.runtime = Runtime(Settings.from_env())
        try:
            yield
        finally:
            await app.state.runtime.close()

    app = FastAPI(title="Residencial Aurora", lifespan=lifespan)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse(
            status_code=404, content={"detail": "Sessão ou apartamento inexistente."}
        )

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse(
            status_code=409,
            content={"detail": "Confirmação não pendente nesta sessão."},
        )

    @app.exception_handler(APIError)
    @app.exception_handler(RuntimeError)
    async def unavailable(request, exc):
        logging.getLogger(__name__).warning(
            "Execução interrompida: %s", type(exc).__name__
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Execução indisponível; decisões aceitas serão reconciliadas na próxima mensagem."
            },
        )

    @app.post("/sessoes", status_code=201)
    async def create(payload: SessionInput):
        return {
            "session_id": await app.state.runtime.create_session(payload.apartamento)
        }

    @app.post("/sessoes/{session_id}/mensagens")
    async def message(session_id: str, payload: MessageInput):
        return await app.state.runtime.message(session_id, payload.texto)

    @app.post("/sessoes/{session_id}/confirmacoes")
    async def confirm(session_id: str, payload: ConfirmationInput):
        return await app.state.runtime.confirm(
            session_id, payload.id, payload.confirmado
        )

    @app.get("/sessoes/{session_id}/eventos")
    async def events(session_id: str):
        return await app.state.runtime.events(session_id)

    def apartment(number):
        store = app.state.runtime.store
        if not store.apartment(number):
            raise HTTPException(status_code=404, detail="Apartamento inexistente.")
        return store

    @app.get("/apartamentos/{apartamento}/reservas")
    async def reservations(apartamento: str):
        return apartment(apartamento).reservations(apartamento)

    @app.get("/apartamentos/{apartamento}/visitantes")
    async def visitors(apartamento: str):
        return apartment(apartamento).visitors(apartamento)

    return app
