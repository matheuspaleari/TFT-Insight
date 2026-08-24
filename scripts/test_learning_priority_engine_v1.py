from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.models.skill_fusion_result import SkillFusionResult
from src.learning.models.skill_level import SkillLevel
from src.learning.models.skill_signal import SkillSignal
from src.learning.services.learning_priority_engine import (
    LearningPriorityEngine,
)


def signal(
    skill_id: str,
    *,
    direction: str,
    confidence: float,
    habit_id: str,
    assessable: bool = False,
    level_hint=None,
) -> SkillSignal:
    return SkillSignal(
        skill_id=skill_id,
        skill_label=skill_id,
        direction=direction,
        confidence=confidence,
        assessable=assessable,
        level_hint=level_hint,
        habit_ids=(habit_id,),
        evidence_ids=("evidence",),
        interpretation="teste",
        limitations=(),
    )


def fusion(
    skill_id: str,
    *,
    level,
    score,
    confidence,
    decision="baseline_only",
    baseline=True,
    signals=(),
) -> SkillFusionResult:
    return SkillFusionResult(
        skill_id=skill_id,
        skill_label=skill_id,
        baseline_available=baseline,
        baseline_level=level if baseline else None,
        baseline_score=score if baseline else None,
        baseline_confidence=confidence if baseline else None,
        fused_level=level,
        fused_score=score,
        fused_confidence=confidence,
        decision=decision,
        supporting_signals=signals,
        evidence_ids=(),
        interpretation="teste",
        limitations=(),
    )


def main() -> None:
    scenarios = []

    # Cenário 1: perfil parecido com o caso real.
    results_real = (
        fusion(
            "leveling",
            level=SkillLevel.DEVELOPING,
            score=35.26,
            confidence=90.0,
            decision="context_added",
            signals=(
                signal(
                    "leveling",
                    direction="positive",
                    confidence=88.03,
                    habit_id="consistent_level_progression",
                ),
            ),
        ),
        fusion(
            "consistency",
            level=SkillLevel.DEVELOPING,
            score=25.25,
            confidence=80.0,
        ),
        fusion(
            "board_pressure",
            level=SkillLevel.ADVANCED,
            score=65.86,
            confidence=90.0,
        ),
        fusion(
            "economy",
            level=SkillLevel.NOT_EVALUATED,
            score=0.0,
            confidence=0.0,
        ),
        fusion(
            "composition_flexibility",
            level=SkillLevel.COMPETENT,
            score=None,
            confidence=53.49,
            decision="candidate_skill",
            baseline=False,
        ),
        fusion(
            "lobby_reading",
            level=None,
            score=None,
            confidence=78.72,
            decision="candidate_context",
            baseline=False,
        ),
    )

    plan = LearningPriorityEngine.build(
        fusion_results=results_real
    )

    scenarios.append(
        (
            "Caso real: consistência antes de leveling",
            (
                plan.primary.skill_id if plan.primary else None,
                tuple(item.skill_id for item in plan.secondary),
                tuple(item.skill_id for item in plan.strengths),
                tuple(item.skill_id for item in plan.context),
            ),
            (
                "consistency",
                ("leveling",),
                ("board_pressure",),
                (
                    "lobby_reading",
                    "composition_flexibility",
                    "economy",
                ),
            ),
        )
    )

    scenarios.append(
        (
            "Leveling positivo refina foco",
            (
                "timing da progressão"
                in next(
                    item
                    for item in (
                        plan.primary,
                        *plan.secondary,
                    )
                    if item.skill_id == "leveling"
                ).training_focus
            ),
            True,
        )
    )

    # Cenário 3: candidato nunca passa uma fraqueza oficial.
    weak_official = fusion(
        "consistency",
        level=SkillLevel.COMPETENT,
        score=45.0,
        confidence=80.0,
    )
    candidate = fusion(
        "composition_flexibility",
        level=SkillLevel.BEGINNER,
        score=None,
        confidence=99.0,
        decision="candidate_skill",
        baseline=False,
    )

    plan_candidate = LearningPriorityEngine.build(
        fusion_results=(
            candidate,
            weak_official,
        )
    )

    scenarios.append(
        (
            "Skill candidata não vira prioridade oficial",
            (
                plan_candidate.primary.skill_id
                if plan_candidate.primary
                else None
            ),
            "consistency",
        )
    )

    # Cenário 4: força não vira correção.
    only_strength = LearningPriorityEngine.build(
        fusion_results=(
            fusion(
                "board_pressure",
                level=SkillLevel.MASTERED,
                score=88.0,
                confidence=90.0,
            ),
        )
    )

    scenarios.append(
        (
            "Força não vira prioridade de correção",
            (
                only_strength.primary,
                tuple(
                    item.skill_id
                    for item in only_strength.strengths
                ),
            ),
            (
                None,
                ("board_pressure",),
            ),
        )
    )

    # Cenário 5: NOT_EVALUATED vira contexto.
    not_eval = LearningPriorityEngine.build(
        fusion_results=(
            fusion(
                "economy",
                level=SkillLevel.NOT_EVALUATED,
                score=0.0,
                confidence=0.0,
            ),
        )
    )

    scenarios.append(
        (
            "Não avaliada não vira prioridade",
            (
                not_eval.primary,
                tuple(
                    item.skill_id
                    for item in not_eval.context
                ),
            ),
            (
                None,
                ("economy",),
            ),
        )
    )

    print("=" * 82)
    print("TFT INSIGHT - LEARNING PRIORITY ENGINE V1 VALIDATION")
    print("=" * 82)

    passed = 0

    for index, (
        name,
        actual,
        expected,
    ) in enumerate(
        scenarios,
        start=1,
    ):
        ok = actual == expected
        passed += int(ok)

        print()
        print(f"[{index}] {name}")
        print(f"Esperado: {expected}")
        print(f"Obtido  : {actual}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(scenarios)}")

    if passed == len(scenarios):
        print("LEARNING PRIORITY ENGINE V1: VALIDADA")
        raise SystemExit(0)

    print("LEARNING PRIORITY ENGINE V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
