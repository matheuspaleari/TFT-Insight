from fastapi import APIRouter

from src.integration_engine.config import (
    IntegrationSettings,
)


router = APIRouter(
    tags=["system"],
)

settings = IntegrationSettings.from_environment()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "api_version": settings.api_version,
        "contract_version": settings.contract_version,
        "environment": settings.environment,
    }


@router.get("/v1/capabilities")
def capabilities() -> dict:
    return {
        "analysis": {
            "overall_score": True,
            "prediction": True,
            "feature_importance": True,
            "recommendations": True,
            "coach": True,
        },
        "contracts": [
            "AnalyzeRequest",
            "AnalyzeResponse",
        ],
        "authentication": "X-API-Key",
    }
