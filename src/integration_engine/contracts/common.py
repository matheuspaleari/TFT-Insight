from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    request_id: str
    api_version: str
    contract_version: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    processing_ms: float


class EvidenceItem(BaseModel):
    key: str
    value: str
    description: str | None = None


class LimitationItem(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    request_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    error_code: str
    message: str
    details: dict[str, Any] = Field(
        default_factory=dict
    )
