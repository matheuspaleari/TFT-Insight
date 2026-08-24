"""
Performance Engine.

Os componentes são carregados sob demanda para evitar dependências
circulares com os serviços da aplicação e o Coach Engine.
"""

from typing import Any


__all__ = [
    "BenchmarkEngine",
    "PerformanceEngine",
]


def __getattr__(name: str) -> Any:
    if name == "BenchmarkEngine":
        from .engine import BenchmarkEngine

        return BenchmarkEngine

    if name == "PerformanceEngine":
        from .engine import PerformanceEngine

        return PerformanceEngine

    raise AttributeError(
        f"O módulo {__name__!r} não possui o atributo {name!r}."
    )