from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ApiUsageEvent:
    request_id: str
    partner_key: str
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    created_at: datetime
    response_bytes: int = 0
    cache_hits: int = 0
    new_downloads: int = 0
    matches_analyzed: int = 0
    error_message: str | None = None
