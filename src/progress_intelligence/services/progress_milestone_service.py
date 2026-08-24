from __future__ import annotations

import hashlib
from typing import Any

from ..models.progress_milestone import ProgressMilestone
from ..models.progress_snapshot import ProgressSnapshot


class ProgressMilestoneService:
    """Detects evidence-backed milestones between two snapshots."""

    LEVEL_ORDER = {
        "NOT_EVALUATED": 0,
        "BEGINNER": 1,
        "DEVELOPING": 2,
        "COMPETENT": 3,
        "ADVANCED": 4,
        "MASTERED": 5,
    }

    @classmethod
    def _make(
        cls,
        *,
        skill_id: str,
        milestone_type: str,
        title: str,
        description: str,
        detected_at: str,
        from_value: Any,
        to_value: Any,
        evidence: dict[str, Any],
    ) -> ProgressMilestone:
        raw = (
            f"{skill_id}|{milestone_type}|{detected_at}|"
            f"{from_value}|{to_value}"
        )
        milestone_id = hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:16]
        return ProgressMilestone(
            milestone_id=f"milestone_{milestone_id}",
            skill_id=skill_id,
            milestone_type=milestone_type,
            title=title,
            description=description,
            detected_at=detected_at,
            from_value=from_value,
            to_value=to_value,
            evidence=evidence,
        )

    @classmethod
    def detect(
        cls,
        *,
        previous: ProgressSnapshot | None,
        current: ProgressSnapshot,
    ) -> list[ProgressMilestone]:
        if previous is None:
            return []

        milestones: list[ProgressMilestone] = []

        for skill_id, current_skill in current.skills.items():
            previous_skill = previous.skills.get(skill_id)
            if not previous_skill:
                continue

            previous_level = str(
                previous_skill.get("level", "NOT_EVALUATED")
            )
            current_level = str(
                current_skill.get("level", "NOT_EVALUATED")
            )

            if (
                cls.LEVEL_ORDER.get(current_level, 0)
                > cls.LEVEL_ORDER.get(previous_level, 0)
            ):
                milestones.append(
                    cls._make(
                        skill_id=skill_id,
                        milestone_type="LEVEL_UP",
                        title=f"{skill_id}: novo nível de domínio",
                        description=(
                            f"A Skill avançou de {previous_level} "
                            f"para {current_level}."
                        ),
                        detected_at=current.created_at,
                        from_value=previous_level,
                        to_value=current_level,
                        evidence={
                            "previous_snapshot_id": previous.snapshot_id,
                            "current_snapshot_id": current.snapshot_id,
                        },
                    )
                )

            previous_trend = str(
                previous_skill.get(
                    "trend",
                    "INSUFFICIENT_HISTORY",
                )
            )
            current_trend = str(
                current_skill.get(
                    "trend",
                    "INSUFFICIENT_HISTORY",
                )
            )

            if (
                current_trend == "IMPROVING"
                and previous_trend != "IMPROVING"
            ):
                milestones.append(
                    cls._make(
                        skill_id=skill_id,
                        milestone_type="IMPROVING_TREND",
                        title=f"{skill_id}: tendência de melhora",
                        description=(
                            "A Skill passou a apresentar tendência "
                            "conclusiva de melhora."
                        ),
                        detected_at=current.created_at,
                        from_value=previous_trend,
                        to_value=current_trend,
                        evidence={
                            "previous_snapshot_id": previous.snapshot_id,
                            "current_snapshot_id": current.snapshot_id,
                            "trend_confidence": current_skill.get(
                                "trend_confidence"
                            ),
                        },
                    )
                )

            previous_difficulty = previous_skill.get(
                "current_difficulty"
            )
            current_difficulty = current_skill.get(
                "current_difficulty"
            )
            difficulty_order = {
                None: 0,
                "FOUNDATION": 1,
                "INTERMEDIATE": 2,
                "ADVANCED": 3,
            }

            if (
                difficulty_order.get(current_difficulty, 0)
                > difficulty_order.get(previous_difficulty, 0)
            ):
                milestones.append(
                    cls._make(
                        skill_id=skill_id,
                        milestone_type="DIFFICULTY_UP",
                        title=f"{skill_id}: treino mais avançado",
                        description=(
                            f"A dificuldade de treino avançou de "
                            f"{previous_difficulty or '-'} para "
                            f"{current_difficulty}."
                        ),
                        detected_at=current.created_at,
                        from_value=previous_difficulty,
                        to_value=current_difficulty,
                        evidence={
                            "previous_snapshot_id": previous.snapshot_id,
                            "current_snapshot_id": current.snapshot_id,
                        },
                    )
                )

        return milestones
