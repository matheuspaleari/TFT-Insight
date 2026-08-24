from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TrainingExercise:
    exercise_id: str
    title: str
    instruction: str
    checklist: tuple[str, ...]
    success_signals: tuple[str, ...]
    system_verification: str

@dataclass(frozen=True)
class TrainingPlan:
    primary_skill_id: str
    primary_skill_label: str
    objective: str
    games_target: int
    exercise: TrainingExercise
    secondary_focus: tuple[str, ...]
    strengths_to_preserve: tuple[str, ...]
    contexts_to_watch: tuple[str, ...]
    rationale: str
    confidence: float
    limitations: tuple[str, ...]
