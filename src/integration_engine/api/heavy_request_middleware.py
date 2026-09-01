from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse

from src.integration_engine.api.heavy_request_queue import (
    HEAVY_REQUEST_QUEUE,
    HeavyRequestQueueFullError,
)


class HeavyRequestQueueMiddleware:
    """
    Serializes expensive POST operations under /v1/.

    GET endpoints remain unaffected, so health checks, capabilities
    and lightweight reads continue responding even while an analysis
    is running.
    """

    def __init__(self, app) -> None:
        self.app = app

    @staticmethod
    def _is_heavy_request(scope: dict) -> bool:
        if scope.get("type") != "http":
            return False

        method = str(
            scope.get("method", "")
        ).upper()

        path = str(
            scope.get("path", "")
        )

        return (
            method == "POST"
            and path.startswith("/v1/")
        )

    async def __call__(
        self,
        scope,
        receive,
        send,
    ) -> None:
        if not self._is_heavy_request(scope):
            await self.app(
                scope,
                receive,
                send,
            )
            return

        try:
            admission = (
                await HEAVY_REQUEST_QUEUE.acquire()
            )

        except HeavyRequestQueueFullError:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "A fila de análises está "
                        "temporariamente cheia. "
                        "Tente novamente em alguns instantes."
                    ),
                    "queue": {
                        "active": (
                            HEAVY_REQUEST_QUEUE.active
                        ),
                        "waiting": (
                            HEAVY_REQUEST_QUEUE.waiting
                        ),
                        "max_waiting": (
                            HEAVY_REQUEST_QUEUE.max_waiting
                        ),
                    },
                },
                headers={
                    "Retry-After": "30",
                },
            )

            await response(
                scope,
                receive,
                send,
            )
            return

        response_started = False

        async def send_with_queue_headers(
            message,
        ) -> None:
            nonlocal response_started

            if (
                message["type"]
                == "http.response.start"
                and not response_started
            ):
                response_started = True

                headers = MutableHeaders(
                    raw=message["headers"]
                )

                headers[
                    "X-TFT-Queue-Waited"
                ] = (
                    "true"
                    if admission.waited
                    else "false"
                )

                headers[
                    "X-TFT-Queue-Wait-Ms"
                ] = str(
                    int(
                        admission.wait_seconds
                        * 1000
                    )
                )

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_queue_headers,
            )

        finally:
            # Critical safety guarantee:
            # even if the analysis crashes, the next queued request
            # is always released.
            await HEAVY_REQUEST_QUEUE.release()