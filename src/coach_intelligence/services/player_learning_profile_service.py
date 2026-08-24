from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.coach_intelligence.models.player_learning_profile import (
    LearningSkillProfile,
    PlayerLearningProfile,
)


class PlayerLearningProfileService:
    VERSION = 1

    @classmethod
    def build(
        cls,
        *,
        assessments,
        pedagogical_memory: dict[str, Any] | None,
        current_priority_skill_id: str | None,
    ) -> PlayerLearningProfile:
        memory = (
            pedagogical_memory
            if isinstance(
                pedagogical_memory,
                dict,
            )
            else {}
        )

        memory_skills = memory.get(
            "skills",
            {},
        )

        if not isinstance(
            memory_skills,
            dict,
        ):
            memory_skills = {}

        assessment_map = {
            str(item.skill.id): item
            for item in assessments
        }

        skill_ids = list(
            assessment_map.keys()
        )

        for skill_id in memory_skills:
            if skill_id not in skill_ids:
                skill_ids.append(
                    skill_id
                )

        profiles = []

        for skill_id in skill_ids:
            assessment = assessment_map.get(
                skill_id
            )
            training = memory_skills.get(
                skill_id,
                {},
            )

            if not isinstance(
                training,
                dict,
            ):
                training = {}

            cycles_total = int(
                training.get(
                    "cycles_total",
                    0,
                )
                or 0
            )

            current_task_id = training.get(
                "current_task_id"
            )

            state = cls._state(
                skill_id=skill_id,
                current_priority_skill_id=(
                    current_priority_skill_id
                ),
                current_task_id=current_task_id,
                cycles_total=cycles_total,
                assessment=assessment,
            )

            if assessment is None:
                skill_name = skill_id.replace(
                    "_",
                    " ",
                ).title()
                score = None
                level = "NOT_EVALUATED"
                confidence = 0.0
                metric_ids = ()
                limitations = (
                    "Skill presente no histórico de treino, mas sem "
                    "SkillAssessment atual.",
                )
            else:
                skill_name = str(
                    getattr(
                        assessment.skill,
                        "title",
                        skill_id,
                    )
                )
                level = cls._level_name(
                    assessment.level
                )
                score = (
                    None
                    if level == "NOT_EVALUATED"
                    else float(
                        assessment.score
                    )
                )
                confidence = float(
                    assessment.confidence
                )
                metric_ids = tuple(
                    str(item)
                    for item in getattr(
                        assessment,
                        "evidence_metric_ids",
                        (),
                    )
                )
                limitations = tuple(
                    str(item)
                    for item in getattr(
                        assessment,
                        "limitations",
                        (),
                    )
                )

            profiles.append(
                LearningSkillProfile(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    state=state,
                    score=score,
                    level=level,
                    assessment_confidence=confidence,
                    trend=str(
                        training.get(
                            "trend",
                            "INSUFFICIENT_HISTORY",
                        )
                    ),
                    trend_confidence=str(
                        training.get(
                            "trend_confidence",
                            "LOW",
                        )
                    ),
                    cycles_total=cycles_total,
                    conclusive_cycles=int(
                        training.get(
                            "conclusive_cycles",
                            0,
                        )
                        or 0
                    ),
                    latest_training_result=(
                        training.get(
                            "latest_result"
                        )
                    ),
                    current_task_id=current_task_id,
                    current_difficulty=(
                        training.get(
                            "current_difficulty"
                        )
                    ),
                    anti_loop_action=str(
                        training.get(
                            "anti_loop_action",
                            "CONTINUE",
                        )
                    ),
                    task_progression=str(
                        training.get(
                            "task_progression",
                            "HOLD",
                        )
                    ),
                    evidence_metric_ids=metric_ids,
                    limitations=limitations,
                )
            )

        return PlayerLearningProfile(
            version=cls.VERSION,
            generated_at=datetime.now(
                timezone.utc
            ).isoformat(),
            current_priority_skill_id=(
                current_priority_skill_id
            ),
            skills=tuple(
                profiles
            ),
        )

    @staticmethod
    def _level_name(
        level,
    ) -> str:
        """
        Normaliza SkillLevel sem depender do tipo do Enum.

        SkillLevel do projeto é IntEnum:
        NOT_EVALUATED=0 ... MASTERED=5.
        Para IntEnum, .value é numérico; portanto usamos .name.
        """
        name = getattr(
            level,
            "name",
            None,
        )

        if name:
            return str(
                name
            ).upper()

        raw = str(
            level
        ).strip()

        if "." in raw:
            raw = raw.rsplit(
                ".",
                1,
            )[-1]

        numeric_names = {
            "0": "NOT_EVALUATED",
            "1": "BEGINNER",
            "2": "DEVELOPING",
            "3": "COMPETENT",
            "4": "ADVANCED",
            "5": "MASTERED",
        }

        return numeric_names.get(
            raw,
            raw.upper(),
        )

    @staticmethod
    def _state(
        *,
        skill_id: str,
        current_priority_skill_id: str | None,
        current_task_id: str | None,
        cycles_total: int,
        assessment,
    ) -> str:
        if (
            skill_id
            == current_priority_skill_id
            or current_task_id
        ):
            return "IN_TRAINING"

        if cycles_total > 0:
            return "TRAINED"

        if assessment is None:
            return "OBSERVED"

        level = PlayerLearningProfileService._level_name(
            getattr(
                assessment,
                "level",
                "NOT_EVALUATED",
            )
        )

        if level == "NOT_EVALUATED":
            return "OBSERVED"

        score = float(
            assessment.score
        )

        if score >= 80.0:
            return "STRONG"

        if score < 40.0:
            return "DEVELOPMENT_OPPORTUNITY"

        return "OBSERVED"
