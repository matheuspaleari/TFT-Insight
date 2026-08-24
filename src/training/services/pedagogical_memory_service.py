from __future__ import annotations

from typing import Any

from src.storage import PlayerRepository
from src.training.services.anti_loop_training_guard import (
    AntiLoopTrainingGuard,
)
from src.training.services.skill_training_history_aggregator import (
    SkillTrainingHistoryAggregator,
)


class PedagogicalMemoryService:
    VERSION = 1

    def __init__(
        self,
        *,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.player_repository = (
            player_repository
            or PlayerRepository()
        )

    def refresh(
        self,
        *,
        puuid: str,
        training_history: list[dict[str, Any]],
        current_mission=None,
    ) -> dict[str, Any]:
        previous = (
            self.player_repository.load_pedagogical_memory(
                puuid=puuid
            )
            or {}
        )

        skill_ids = list(
            SkillTrainingHistoryAggregator.aggregate_all(
                training_history=training_history
            ).keys()
        )

        current_skill_id = None
        current_task_id = None
        current_difficulty = None
        current_progress = None

        if current_mission is not None:
            current_skill_id = str(
                current_mission.skill_id
            )
            current_task_id = str(
                current_mission.task.id
            )
            current_difficulty = str(
                getattr(
                    current_mission.task,
                    "difficulty",
                    "FOUNDATION",
                )
            )
            current_progress = {
                "games_completed": int(
                    current_mission.games_completed
                ),
                "games_target": int(
                    current_mission.games_target
                ),
                "is_completed": bool(
                    current_mission.is_completed
                ),
            }

            if current_skill_id not in skill_ids:
                skill_ids.append(
                    current_skill_id
                )

        skills: dict[str, Any] = {}

        for skill_id in skill_ids:
            summary = (
                SkillTrainingHistoryAggregator.aggregate(
                    skill_id=skill_id,
                    training_history=training_history,
                )
            )

            guard = AntiLoopTrainingGuard.evaluate(
                skill_id=skill_id,
                training_history=training_history,
            )

            last_cycle = (
                summary.cycles[0]
                if summary.cycles
                else None
            )

            skills[skill_id] = {
                "cycles_total": summary.cycles_total,
                "evaluated_cycles": summary.evaluated_cycles,
                "conclusive_cycles": summary.conclusive_cycles,
                "positive_cycles": summary.positive_cycles,
                "stable_cycles": summary.stable_cycles,
                "negative_cycles": summary.negative_cycles,
                "inconclusive_cycles": summary.inconclusive_cycles,
                "trend": summary.trend,
                "trend_confidence": (
                    summary.trend_confidence
                ),
                "latest_result": summary.latest_result,
                "anti_loop_action": guard.action,
                "task_progression": (
                    guard.task_progression
                ),
                "consecutive_skill_cycles": (
                    guard.consecutive_skill_cycles
                ),
                "last_task_id": (
                    last_cycle.task_id
                    if last_cycle
                    else None
                ),
                "last_task_title": (
                    last_cycle.task_title
                    if last_cycle
                    else None
                ),
                "current_task_id": (
                    current_task_id
                    if skill_id == current_skill_id
                    else None
                ),
                "current_difficulty": (
                    current_difficulty
                    if skill_id == current_skill_id
                    else None
                ),
                "rationale": summary.rationale,
            }

        memory = {
            "version": self.VERSION,
            "updated_at": (
                self.player_repository._utc_now()
            ),
            "current_skill_id": current_skill_id,
            "current_mission": (
                {
                    "skill_id": current_skill_id,
                    "task_id": current_task_id,
                    "difficulty": current_difficulty,
                    **(
                        current_progress
                        or {}
                    ),
                }
                if current_skill_id
                else None
            ),
            "skills": skills,
            "last_decision": previous.get(
                "last_decision"
            ),
        }

        self.player_repository.save_pedagogical_memory(
            puuid=puuid,
            memory=memory,
        )

        return memory

    def record_decision(
        self,
        *,
        puuid: str,
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        memory = (
            self.player_repository.load_pedagogical_memory(
                puuid=puuid
            )
            or {
                "version": self.VERSION,
                "skills": {},
            }
        )

        memory["version"] = self.VERSION
        memory["updated_at"] = (
            self.player_repository._utc_now()
        )
        memory["last_decision"] = decision

        self.player_repository.save_pedagogical_memory(
            puuid=puuid,
            memory=memory,
        )

        return memory

    @staticmethod
    def public_payload(
        memory: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(
            memory,
            dict,
        ):
            return None

        public_skills: dict[str, Any] = {}

        raw_skills = memory.get(
            "skills",
            {},
        )

        if isinstance(
            raw_skills,
            dict,
        ):
            for skill_id, item in raw_skills.items():
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                public_skills[str(skill_id)] = {
                    "cycles_total": int(
                        item.get(
                            "cycles_total",
                            0,
                        )
                        or 0
                    ),
                    "evaluated_cycles": int(
                        item.get(
                            "evaluated_cycles",
                            0,
                        )
                        or 0
                    ),
                    "conclusive_cycles": int(
                        item.get(
                            "conclusive_cycles",
                            0,
                        )
                        or 0
                    ),
                    "trend": str(
                        item.get(
                            "trend",
                            "INSUFFICIENT_HISTORY",
                        )
                    ),
                    "trend_confidence": str(
                        item.get(
                            "trend_confidence",
                            "LOW",
                        )
                    ),
                    "latest_result": item.get(
                        "latest_result"
                    ),
                    "anti_loop_action": str(
                        item.get(
                            "anti_loop_action",
                            "CONTINUE",
                        )
                    ),
                    "task_progression": str(
                        item.get(
                            "task_progression",
                            "HOLD",
                        )
                    ),
                    "consecutive_skill_cycles": int(
                        item.get(
                            "consecutive_skill_cycles",
                            0,
                        )
                        or 0
                    ),
                    "last_task_id": item.get(
                        "last_task_id"
                    ),
                    "last_task_title": item.get(
                        "last_task_title"
                    ),
                    "current_task_id": item.get(
                        "current_task_id"
                    ),
                    "current_difficulty": item.get(
                        "current_difficulty"
                    ),
                }

        last_decision = memory.get(
            "last_decision"
        )

        if not isinstance(
            last_decision,
            dict,
        ):
            last_decision = None

        return {
            "version": int(
                memory.get(
                    "version",
                    1,
                )
                or 1
            ),
            "current_skill_id": memory.get(
                "current_skill_id"
            ),
            "skills": public_skills,
            "last_decision": last_decision,
        }
