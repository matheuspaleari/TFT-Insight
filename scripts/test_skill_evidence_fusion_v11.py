from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.models.skill_level import SkillLevel
from src.learning.models.skill_signal import SkillSignal
from src.learning.services.skill_evidence_fusion_service import (
    SkillEvidenceFusionService,
)


@dataclass(frozen=True)
class FakeSkill:
    id: str
    title: str


@dataclass(frozen=True)
class FakeAssessment:
    skill: FakeSkill
    score: float
    level: SkillLevel
    confidence: float
    evidence_metric_ids: tuple[str, ...]
    limitations: tuple[str, ...]


def assessment(skill_id, level, score, confidence):
    return FakeAssessment(
        skill=FakeSkill(
            id=skill_id,
            title=skill_id,
        ),
        score=score,
        level=level,
        confidence=confidence,
        evidence_metric_ids=("performance_metric",),
        limitations=("limitação base",),
    )


def signal(skill_id, level, confidence, assessable=True, direction="positive"):
    return SkillSignal(
        skill_id=skill_id,
        skill_label=skill_id,
        direction=direction,
        confidence=confidence,
        assessable=assessable,
        level_hint=level,
        habit_ids=("habit",),
        evidence_ids=("habit_evidence",),
        interpretation="signal",
        limitations=("limitação signal",),
    )


def main():
    scenarios = [
        (
            "Mesmo nível reforça confiança",
            (assessment("leveling", SkillLevel.ADVANCED, 72.0, 90.0),),
            (signal("leveling", SkillLevel.ADVANCED, 88.0),),
            ("reinforced", SkillLevel.ADVANCED, 94.4),
        ),
        (
            "Divergência preserva assessment",
            (assessment("leveling", SkillLevel.COMPETENT, 55.0, 90.0),),
            (signal("leveling", SkillLevel.ADVANCED, 88.0),),
            ("evidence_disagreement", SkillLevel.COMPETENT, 90.0),
        ),
        (
            "Contexto não altera Skill",
            (assessment("economy", SkillLevel.NOT_EVALUATED, 0.0, 0.0),),
            (signal("economy", None, 80.0, False, "context"),),
            ("context_only", SkillLevel.NOT_EVALUATED, 0.0),
        ),
        (
            "Nova Skill avaliável fica candidata",
            (),
            (signal("composition_flexibility", SkillLevel.COMPETENT, 54.0),),
            ("candidate_skill", SkillLevel.COMPETENT, 54.0),
        ),
        (
            "Lobby reading fica somente contexto",
            (),
            (signal("lobby_reading", None, 79.0, False, "context"),),
            ("candidate_context", None, 79.0),
        ),
    ]

    print("=" * 78)
    print("TFT INSIGHT - SKILL EVIDENCE FUSION V1.1 VALIDATION")
    print("=" * 78)

    passed = 0

    for index, (name, assessments, signals, expected) in enumerate(
        scenarios,
        start=1,
    ):
        result = SkillEvidenceFusionService.fuse(
            assessments=assessments,
            signals=signals,
        )[0]

        actual = (
            result.decision,
            result.fused_level,
            result.fused_confidence,
        )

        ok = actual == expected
        passed += int(ok)

        print()
        print(f"[{index}] {name}")
        print(f"Esperado: {expected}")
        print(f"Obtido  : {actual}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 78)
    print(f"PASSARAM: {passed}/{len(scenarios)}")

    if passed == len(scenarios):
        print("SKILL EVIDENCE FUSION V1.1: VALIDADA")
        raise SystemExit(0)

    print("SKILL EVIDENCE FUSION V1.1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
