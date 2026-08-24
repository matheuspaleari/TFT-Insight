from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SDKModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        frozen=True,
    )


class ApiMeta(SDKModel):
    request_id: str
    api_version: str
    contract_version: str
    generated_at: datetime
    processing_ms: float


class EvidenceItem(SDKModel):
    key: str
    value: str
    description: str | None = None


class LimitationItem(SDKModel):
    code: str
    message: str


class HealthResponse(SDKModel):
    status: str
    service: str
    api_version: str
    contract_version: str
    environment: str


class CapabilitiesResponse(SDKModel):
    analysis: dict[str, bool]
    contracts: list[str]
    authentication: str


class ErrorPayload(SDKModel):
    request_id: str | None = None
    error_code: str | None = None
    message: str | None = None
    detail: Any | None = None
    details: dict[str, Any] = Field(default_factory=dict)
