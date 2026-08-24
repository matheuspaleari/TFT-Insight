from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LearningSkillProfile:
    skill_id: str
    skill_name: str
    state: str
    score: float | None
    level: str
    assessment_confidence: float
    trend: str
    trend_confidence: str
    cycles_total: int
    conclusive_cycles: int
    latest_training_result: str | None
    current_task_id: str | None
    current_difficulty: str | None
    anti_loop_action: str
    task_progression: str
    evidence_metric_ids: tuple[str, ...] = field(
        default_factory=tuple
    )
    limitations: tuple[str, ...] = field(
        default_factory=tuple
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "state": self.state,
            "score": self.score,
            "level": self.level,
            "assessment_confidence": self.assessment_confidence,
            "trend": self.trend,
            "trend_confidence": self.trend_confidence,
            "cycles_total": self.cycles_total,
            "conclusive_cycles": self.conclusive_cycles,
            "latest_training_result": self.latest_training_result,
            "current_task_id": self.current_task_id,
            "current_difficulty": self.current_difficulty,
            "anti_loop_action": self.anti_loop_action,
            "task_progression": self.task_progression,
            "evidence_metric_ids": list(
                self.evidence_metric_ids
            ),
            "limitations": list(
                self.limitations
            ),
        }


@dataclass(frozen=True, slots=True)
class PlayerLearningProfile:
    version: int
    generated_at: str
    current_priority_skill_id: str | None
    skills: tuple[LearningSkillProfile, ...]

    def get_skill(
        self,
        skill_id: str,
    ) -> LearningSkillProfile | None:
        return next(
            (
                item
                for item in self.skills
                if item.skill_id == skill_id
            ),
            None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "current_priority_skill_id": (
                self.current_priority_skill_id
            ),
            "skills": {
                item.skill_id: item.to_dict()
                for item in self.skills
            },
        }
