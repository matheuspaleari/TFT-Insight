from fastapi import APIRouter, status

from src.integration_engine.contracts.overwolf_events import (
    OverwolfEventRequest,
    OverwolfEventResponse,
)
from src.integration_engine.overwolf.normalizer import normalize_overwolf_event

router = APIRouter(prefix="/v1/overwolf", tags=["overwolf"])


@router.post(
    "/events",
    response_model=OverwolfEventResponse,
    status_code=status.HTTP_200_OK,
)
def receive_overwolf_event(request: OverwolfEventRequest) -> OverwolfEventResponse:
    normalized = normalize_overwolf_event(request)
    return OverwolfEventResponse(accepted=True, event=normalized)
