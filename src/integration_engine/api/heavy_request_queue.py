from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from time import monotonic


class HeavyRequestQueueFullError(RuntimeError):
    """Raised when the heavy-request waiting queue is full."""


@dataclass(frozen=True)
class QueueAdmission:
    waited: bool
    wait_seconds: float


class HeavyRequestQueue:
    """
    FIFO queue for expensive TFT Insight operations.

    Production policy:
    - 1 heavy request executing at a time.
    - up to 10 waiting.
    """

    def __init__(
        self,
        *,
        max_concurrent: int = 1,
        max_waiting: int = 10,
    ) -> None:
        if max_concurrent < 1:
            raise ValueError(
                "max_concurrent must be >= 1."
            )

        if max_waiting < 0:
            raise ValueError(
                "max_waiting must be >= 0."
            )

        self._max_concurrent = max_concurrent
        self._max_waiting = max_waiting

        self._active = 0
        self._waiting: deque[object] = deque()

        self._condition = asyncio.Condition()

    @property
    def active(self) -> int:
        return self._active

    @property
    def waiting(self) -> int:
        return len(self._waiting)

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    @property
    def max_waiting(self) -> int:
        return self._max_waiting

    def snapshot(self) -> dict[str, int | bool]:
        return {
            "active": self._active,
            "waiting": len(self._waiting),
            "max_concurrent": self._max_concurrent,
            "max_waiting": self._max_waiting,
            "busy": (
                self._active >= self._max_concurrent
            ),
        }

    async def acquire(self) -> QueueAdmission:
        started_waiting_at = monotonic()
        ticket = object()

        async with self._condition:
            if (
                self._active < self._max_concurrent
                and not self._waiting
            ):
                self._active += 1

                return QueueAdmission(
                    waited=False,
                    wait_seconds=0.0,
                )

            if len(self._waiting) >= self._max_waiting:
                raise HeavyRequestQueueFullError(
                    "A fila de análises está temporariamente cheia."
                )

            self._waiting.append(ticket)

            while True:
                is_first = (
                    bool(self._waiting)
                    and self._waiting[0] is ticket
                )

                has_capacity = (
                    self._active < self._max_concurrent
                )

                if is_first and has_capacity:
                    self._waiting.popleft()
                    self._active += 1

                    return QueueAdmission(
                        waited=True,
                        wait_seconds=(
                            monotonic()
                            - started_waiting_at
                        ),
                    )

                try:
                    await self._condition.wait()

                except asyncio.CancelledError:
                    try:
                        self._waiting.remove(ticket)
                    except ValueError:
                        pass

                    self._condition.notify_all()
                    raise

    async def release(self) -> None:
        async with self._condition:
            if self._active > 0:
                self._active -= 1

            self._condition.notify_all()


HEAVY_REQUEST_QUEUE = HeavyRequestQueue(
    max_concurrent=1,
    max_waiting=10,
)