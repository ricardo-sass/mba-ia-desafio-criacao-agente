"""Payloads HTTP; decisão aceita somente booleano JSON."""

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionInput(Payload):
    apartamento: str = Field(min_length=1, max_length=20)


class MessageInput(Payload):
    texto: str = Field(min_length=1, max_length=8000)


class ConfirmationInput(Payload):
    id: str = Field(min_length=1, max_length=200)
    confirmado: StrictBool
