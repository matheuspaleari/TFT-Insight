from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.learning.models.habit import (
    Habit,
    HabitEvidence,
)
from src.learning.models.skill_level import (
    SkillLevel,
)
from src.learning.services.habit_skill_mapping_service import (
    HabitSkillMappingService,
)


def habit(
    habit_id: str,
    *,
    category: str,
    direction: str,
    status: str,
    confidence: float,
) -> Habit:
    return Habit(
        habit_id=habit_id,
        category=category,
        label=habit_id,
        direction=direction,
        status=status,
        confidence=confidence,
        interpretation="teste",
        evidence=(
            HabitEvidence(
                key="evidence",
                label="Evidence",
                value=1,
            ),
        ),
    )


SCENARIOS = [
    (
        "Leveling positivo estabelecido",
        (
            habit(
                "consistent_level_progression",
                category="economy",
                direction="positive",
                status="established",
                confidence=88.0,
            ),
        ),
        {
            "leveling": (
                True,
                SkillLevel.ADVANCED,
                "positive",
            )
        },
    ),
    (
        "Leveling tardio limitado",
        (
            habit(
                "late_low_level_pattern",
                category="economy",
                direction="negative",
                status="observed",
                confidence=75.0,
            ),
        ),
        {
            "leveling": (
                True,
                SkillLevel.DEVELOPING,
                "negative",
            )
        },
    ),
    (
        "Variedade de composição",
        (
            habit(
                "composition_variety",
                category="composition",
                direction="positive",
                status="observed",
                confidence=54.0,
            ),
        ),
        {
            "composition_flexibility": (
                True,
                SkillLevel.COMPETENT,
                "positive",
            )
        },
    ),
    (
        "Flexibilidade estabelecida",
        (
            habit(
                "composition_flexibility",
                category="composition",
                direction="positive",
                status="established",
                confidence=70.0,
            ),
        ),
        {
            "composition_flexibility": (
                True,
                SkillLevel.ADVANCED,
                "positive",
            )
        },
    ),
    (
        "Contestação não mede leitura de lobby",
        (
            habit(
                "recurring_carry_contest_exposure",
                category="contest",
                direction="negative",
                status="established",
                confidence=83.0,
            ),
        ),
        {
            "lobby_reading": (
                False,
                None,
                "context",
            )
        },
    ),
    (
        "Ouro final não mede economia diretamente",
        (
            habit(
                "resources_remaining_at_end",
                category="economy",
                direction="negative",
                status="observed",
                confidence=80.0,
            ),
        ),
        {
            "economy": (
                False,
                None,
                "context",
            )
        },
    ),
]


def main() -> None:
    print("=" * 78)
    print("TFT INSIGHT - SKILL INTEGRATION V1 VALIDATION")
    print("=" * 78)

    passed = 0

    for index, (
        name,
        habits,
        expected,
    ) in enumerate(
        SCENARIOS,
        start=1,
    ):
        signals = HabitSkillMappingService.map(
            habits=habits
        )

        actual = {
            signal.skill_id: (
                signal.assessable,
                signal.level_hint,
                signal.direction,
            )
            for signal in signals
        }

        ok = actual == expected

        print()
        print(f"[{index}] {name}")
        print(f"Esperado: {expected}")
        print(f"Obtido  : {actual}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

        if ok:
            passed += 1

    print()
    print("=" * 78)
    print(f"PASSARAM: {passed}/{len(SCENARIOS)}")

    if passed == len(SCENARIOS):
        print("SKILL INTEGRATION V1: VALIDADA")
        raise SystemExit(0)

    print("SKILL INTEGRATION V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
