from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.models.skill_level import SkillLevel
from src.learning.models.skill_signal import SkillSignal
from src.learning.services.habit_skill_mapping_service import (
    HabitSkillMappingService,
)
from src.learning.services.skill_evidence_fusion_service import (
    SkillEvidenceFusionService,
)


@dataclass(frozen=True)
class Evidence:
    key: str


@dataclass(frozen=True)
class Habit:
    habit_id: str
    category: str
    label: str
    direction: str
    status: str
    confidence: float
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class Skill:
    id: str
    title: str


@dataclass(frozen=True)
class Assessment:
    skill: Skill
    score: float
    level: SkillLevel
    confidence: float
    evidence_metric_ids: tuple[str, ...]
    limitations: tuple[str, ...]


def make_habit(
    habit_id: str,
    *,
    direction: str,
    status: str,
    confidence: float,
) -> Habit:
    return Habit(
        habit_id=habit_id,
        category="test",
        label=habit_id,
        direction=direction,
        status=status,
        confidence=confidence,
        evidence=(Evidence("habit_evidence"),),
    )


def main() -> None:
    print("=" * 80)
    print("TFT INSIGHT - SKILL INTEGRATION V1.1 VALIDATION")
    print("=" * 80)

    passed = 0
    total = 4

    leveling_habit = make_habit(
        "consistent_level_progression",
        direction="positive",
        status="established",
        confidence=88.03,
    )

    leveling_signal = HabitSkillMappingService.map(
        habits=(leveling_habit,)
    )[0]

    ok1 = (
        leveling_signal.skill_id == "leveling"
        and leveling_signal.direction == "positive"
        and leveling_signal.assessable is False
        and leveling_signal.level_hint is None
    )

    print()
    print("[1] Progressão consistente vira suporte, não nível")
    print(
        "Obtido  : "
        f"{leveling_signal.direction}, "
        f"avaliável={leveling_signal.assessable}, "
        f"nível={leveling_signal.level_hint}"
    )
    print(f"Status  : {'OK' if ok1 else 'ERRO'}")
    passed += int(ok1)

    assessment = Assessment(
        skill=Skill(
            id="leveling",
            title="Leveling",
        ),
        score=35.26,
        level=SkillLevel.DEVELOPING,
        confidence=90.0,
        evidence_metric_ids=("level",),
        limitations=("baseline",),
    )

    fusion = SkillEvidenceFusionService.fuse(
        assessments=(assessment,),
        signals=(leveling_signal,),
    )[0]

    ok2 = (
        fusion.decision == "context_added"
        and fusion.fused_level == SkillLevel.DEVELOPING
        and fusion.fused_score == 35.26
        and fusion.fused_confidence == 90.0
    )

    print()
    print("[2] Leveling real preserva assessment e adiciona suporte")
    print(
        "Obtido  : "
        f"{fusion.decision}, "
        f"nível={fusion.fused_level}, "
        f"score={fusion.fused_score}, "
        f"confiança={fusion.fused_confidence}"
    )
    print(f"Status  : {'OK' if ok2 else 'ERRO'}")
    passed += int(ok2)

    composition_habit = make_habit(
        "composition_variety",
        direction="positive",
        status="observed",
        confidence=53.49,
    )

    composition_signal = HabitSkillMappingService.map(
        habits=(composition_habit,)
    )[0]

    ok3 = (
        composition_signal.skill_id == "composition_flexibility"
        and composition_signal.assessable is True
        and composition_signal.level_hint == SkillLevel.COMPETENT
    )

    print()
    print("[3] Composition continua como candidata avaliável")
    print(
        "Obtido  : "
        f"{composition_signal.skill_id}, "
        f"avaliável={composition_signal.assessable}, "
        f"nível={composition_signal.level_hint}"
    )
    print(f"Status  : {'OK' if ok3 else 'ERRO'}")
    passed += int(ok3)

    lobby_habit = make_habit(
        "recurring_carry_contest_exposure",
        direction="neutral",
        status="observed",
        confidence=78.72,
    )

    lobby_signal = HabitSkillMappingService.map(
        habits=(lobby_habit,)
    )[0]

    ok4 = (
        lobby_signal.skill_id == "lobby_reading"
        and lobby_signal.assessable is False
        and lobby_signal.level_hint is None
        and lobby_signal.direction == "context"
    )

    print()
    print("[4] Lobby reading continua apenas contexto")
    print(
        "Obtido  : "
        f"{lobby_signal.direction}, "
        f"avaliável={lobby_signal.assessable}, "
        f"nível={lobby_signal.level_hint}"
    )
    print(f"Status  : {'OK' if ok4 else 'ERRO'}")
    passed += int(ok4)

    print()
    print("=" * 80)
    print(f"PASSARAM: {passed}/{total}")

    if passed == total:
        print("SKILL INTEGRATION V1.1: VALIDADA")
        raise SystemExit(0)

    print("SKILL INTEGRATION V1.1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
