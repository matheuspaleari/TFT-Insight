from typing import Any

from pydantic import BaseModel, Field


class OverwolfEventRequest(BaseModel):
    captured_at: str = Field(..., min_length=1, description="Timestamp ISO-8601 informado pelo collector.")
    kind: str = Field(..., min_length=1, description="Tipo de evento recebido do Overwolf GEP.")
    game_id: int | str | None = Field(default=None, description="Identificador do jogo informado pelo Overwolf.")
    args: list[Any] = Field(default_factory=list, description="Argumentos originais recebidos do evento GEP.")


class NormalizedOverwolfEvent(BaseModel):
    schema_version: str = "1.0"
    source: str = "overwolf_gep"
    captured_at: str
    kind: str
    game_id: int | str | None = None
    category: str
    payload: list[Any] = Field(default_factory=list)


class OverwolfEventResponse(BaseModel):
    accepted: bool
    event: NormalizedOverwolfEvent
