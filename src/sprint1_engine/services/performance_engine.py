from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

from src.sprint1_engine.models import PerformanceMeasurement
from src.sprint1_engine.repositories import KnowledgeRepository


class EnginePerformanceMonitor:
    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self.repository = repository
        self.measurements: list[PerformanceMeasurement] = []

    @contextmanager
    def measure(
        self,
        operation: str,
        *,
        metadata: tuple[str, ...] = (),
    ) -> Iterator[None]:
        started = perf_counter()
        success = False
        try:
            yield
            success = True
        finally:
            elapsed_ms = (perf_counter() - started) * 1000.0
            measurement = PerformanceMeasurement(
                operation=operation,
                elapsed_ms=round(elapsed_ms, 3),
                success=success,
                metadata=metadata,
            )
            self.measurements.append(measurement)
            if self.repository is not None:
                self.repository.save_performance_measurement(measurement)
