"""
Serviços da aplicação.

Os componentes são carregados sob demanda para evitar dependências
circulares entre Services, Performance Engine, Learning Engine
e Coach Engine.
"""

from typing import Any


__all__ = [
    "HistoryService",
    "HomeService",
    "PlayerAnalysisService",
    "PriorityService",
    "RecommendationService",
]


def __getattr__(name: str) -> Any:
    if name == "HistoryService":
        from .history_service import HistoryService

        return HistoryService

    if name == "HomeService":
        from .home_service import HomeService

        return HomeService

    if name == "PlayerAnalysisService":
        from .player_analysis_service import PlayerAnalysisService

        return PlayerAnalysisService

    if name == "PriorityService":
        from .priority_service import PriorityService

        return PriorityService

    if name == "RecommendationService":
        from .recommendation_service import RecommendationService

        return RecommendationService

    raise AttributeError(
        f"O módulo {__name__!r} não possui o atributo {name!r}."
    )