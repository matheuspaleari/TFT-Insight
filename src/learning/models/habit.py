from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HabitEvidence:
    key: str
    label: str
    value: Any
    unit: str = ""


@dataclass(frozen=True)
class Habit:
    """
    Comportamento recorrente observado pelo TFT Insight.

    Um Habit descreve somente padrões sustentados pelo histórico.
    Ele não representa intenção, percepção subjetiva ou uma decisão
    que os dados atuais não permitam observar diretamente.
    """

    habit_id: str
    category: str
    label: str
    direction: str
    status: str
    confidence: float
    interpretation: str
    evidence: tuple[HabitEvidence, ...]

    # Integração futura com o catálogo de Skills.
    related_skill_id: str | None = None
    related_skill_hint: str | None = None


@dataclass(frozen=True)
class HabitDiagnostic:
    category: str
    declared_habit_id: str | None
    status: str
    explanation: str
    checks: tuple[str, ...]
