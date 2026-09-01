from fastapi import APIRouter, Depends

from src.integration_engine.api.dependencies import (
    require_api_key,
)
from src.integration_engine.api.heavy_request_queue import (
    HEAVY_REQUEST_QUEUE,
)


router = APIRouter(
    prefix="/v1/queue",
    tags=["queue"],
)


@router.get("/status")
def queue_status(
    _: str = Depends(require_api_key),
) -> dict[str, int | bool]:
    return HEAVY_REQUEST_QUEUE.snapshot()