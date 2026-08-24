from __future__ import annotations

from datetime import datetime, timezone
import json
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .models import ApiUsageEvent
from .repository import PartnerAnalyticsRepository


class PartnerAnalyticsMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        repository: PartnerAnalyticsRepository | None = None,
    ) -> None:
        super().__init__(app)
        self.repository = (
            repository or PartnerAnalyticsRepository()
        )
        self.repository.initialize()

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        started = perf_counter()

        request_id = (
            request.headers.get("X-Request-ID")
            or str(uuid4())
        )

        status_code = 500
        body = b""
        error_message = None

        try:
            response = await call_next(request)
            status_code = response.status_code

            async for chunk in response.body_iterator:
                body += chunk

            headers = dict(response.headers)
            headers["X-Request-ID"] = request_id

            response = Response(
                content=body,
                status_code=status_code,
                headers=headers,
                media_type=response.media_type,
            )

        except Exception as error:
            error_message = str(error)
            raise

        finally:
            cache_hits = 0
            new_downloads = 0
            matches_analyzed = 0

            if body:
                try:
                    payload = json.loads(body)
                    cache = payload.get("cache", {})

                    cache_hits = int(
                        cache.get("cached_matches_used", 0)
                    )
                    new_downloads = int(
                        cache.get("new_matches_downloaded", 0)
                    )
                    matches_analyzed = int(
                        payload.get("matches_analyzed", 0)
                    )
                except Exception:
                    pass

            event = ApiUsageEvent(
                request_id=request_id,
                partner_key=self._mask_key(
                    request.headers.get("X-API-Key")
                ),
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                latency_ms=round(
                    (perf_counter() - started) * 1000.0,
                    3,
                ),
                created_at=datetime.now(timezone.utc),
                response_bytes=len(body),
                cache_hits=cache_hits,
                new_downloads=new_downloads,
                matches_analyzed=matches_analyzed,
                error_message=error_message,
            )

            try:
                self.repository.record(event)
            except Exception:
                pass

        return response

    @staticmethod
    def _mask_key(value: str | None) -> str:
        if not value:
            return "development"

        if len(value) <= 8:
            return value[:2] + "***"

        return value[:4] + "***" + value[-4:]
