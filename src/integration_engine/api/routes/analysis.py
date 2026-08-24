from fastapi import (
    APIRouter,
    Depends,
)

from src.integration_engine.api.dependencies import (
    require_api_key,
)
from src.integration_engine.contracts import (
    AnalyzeRequest,
    AnalyzeResponse,
)
from src.integration_engine.services import (
    InsightEngine,
)


router = APIRouter(
    prefix="/v1",
    tags=["analysis"],
)

engine = InsightEngine()


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
def analyze(
    request: AnalyzeRequest,
    _: str = Depends(require_api_key),
) -> AnalyzeResponse:
    return engine.analyze(request)
