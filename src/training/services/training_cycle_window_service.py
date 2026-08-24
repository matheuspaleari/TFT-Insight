from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.integration_engine.services.cached_match_service import (
    CachedMatchService,
    MatchLoadResult,
)


@dataclass(frozen=True, slots=True)
class TrainingCycleWindow:
    label: str
    match_ids: tuple[str, ...]
    load_result: MatchLoadResult

    @property
    def requested_count(self) -> int:
        return len(self.match_ids)

    @property
    def loaded_count(self) -> int:
        return len(self.load_result.matches)

    @property
    def coverage(self) -> float:
        if not self.requested_count:
            return 0.0
        return round(
            self.loaded_count / self.requested_count * 100.0,
            2,
        )


@dataclass(frozen=True, slots=True)
class TrainingCycleWindows:
    cycle_id: str
    skill_id: str
    task_id: str
    task_title: str
    related_metric_ids: tuple[str, ...]
    before: TrainingCycleWindow
    after: TrainingCycleWindow


class TrainingCycleWindowService:
    @classmethod
    def reconstruct(
        cls,
        *,
        puuid: str,
        cycle: dict[str, Any],
        cached_match_service: CachedMatchService,
    ) -> TrainingCycleWindows:
        if str(cycle.get("status", "")).lower() != "completed":
            raise ValueError(
                "O Before/After só pode ser reconstruído para ciclo concluído."
            )

        mission = cycle.get("mission")
        if not isinstance(mission, dict):
            raise ValueError("O ciclo não possui mission válida.")

        before_ids = tuple(
            str(x) for x in mission.get("baseline_match_ids", [])
            if str(x).strip()
        )
        after_ids = tuple(
            str(x) for x in mission.get("completed_match_ids", [])
            if str(x).strip()
        )

        if not before_ids:
            raise ValueError("O ciclo não possui baseline_match_ids.")
        if not after_ids:
            raise ValueError("O ciclo não possui completed_match_ids.")

        task = mission.get("task", {})
        if not isinstance(task, dict):
            task = {}

        before_result = cached_match_service.load_matches_by_ids(
            puuid=puuid,
            match_ids=before_ids,
        )
        after_result = cached_match_service.load_matches_by_ids(
            puuid=puuid,
            match_ids=after_ids,
        )

        return TrainingCycleWindows(
            cycle_id=str(cycle.get("cycle_id", mission.get("mission_id", ""))),
            skill_id=str(task.get("skill_id", "")),
            task_id=str(task.get("id", "")),
            task_title=str(task.get("title", "Ciclo de treinamento")),
            related_metric_ids=tuple(
                str(x) for x in task.get("related_metric_ids", [])
            ),
            before=TrainingCycleWindow(
                label="before",
                match_ids=before_ids,
                load_result=before_result,
            ),
            after=TrainingCycleWindow(
                label="after",
                match_ids=after_ids,
                load_result=after_result,
            ),
        )
