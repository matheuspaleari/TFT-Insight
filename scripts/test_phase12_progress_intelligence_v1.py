from __future__ import annotations

from src.progress_intelligence.models.progress_snapshot import (
    ProgressSnapshot,
)
from src.progress_intelligence.services.progress_intelligence_service import (
    ProgressIntelligenceService,
)
from src.progress_intelligence.services.skill_progress_timeline_service import (
    SkillProgressTimelineService,
)
from src.progress_intelligence.services.overall_player_development_service import (
    OverallPlayerDevelopmentService,
)


def snapshot(
    *,
    snapshot_id: str,
    created_at: str,
    leveling_score: float,
    leveling_level: str,
    leveling_trend: str,
    consistency_score: float,
    consistency_trend: str,
):
    return ProgressSnapshot(
        snapshot_id=snapshot_id,
        created_at=created_at,
        priority_skill_id="leveling",
        archived_cycles_total=2,
        skills={
            "leveling": {
                "score": leveling_score,
                "level": leveling_level,
                "trend": leveling_trend,
                "trend_confidence": "MODERATE",
                "cycles_total": 2,
                "conclusive_cycles": 2,
                "current_difficulty": "FOUNDATION",
            },
            "consistency": {
                "score": consistency_score,
                "level": "DEVELOPING",
                "trend": consistency_trend,
                "trend_confidence": "MODERATE",
                "cycles_total": 2,
                "conclusive_cycles": 1,
                "current_difficulty": None,
            },
            "economy": {
                "score": None,
                "level": "NOT_EVALUATED",
                "trend": "INSUFFICIENT_HISTORY",
                "trend_confidence": "LOW",
                "cycles_total": 0,
                "conclusive_cycles": 0,
                "current_difficulty": None,
            },
        },
    )


def main():
    s1 = snapshot(
        snapshot_id="s1",
        created_at="2026-08-01T10:00:00+00:00",
        leveling_score=15.0,
        leveling_level="BEGINNER",
        leveling_trend="INSUFFICIENT_HISTORY",
        consistency_score=30.0,
        consistency_trend="INSUFFICIENT_HISTORY",
    )
    s2 = snapshot(
        snapshot_id="s2",
        created_at="2026-08-10T10:00:00+00:00",
        leveling_score=22.0,
        leveling_level="BEGINNER",
        leveling_trend="IMPROVING",
        consistency_score=31.0,
        consistency_trend="STABLE",
    )
    s3 = snapshot(
        snapshot_id="s3",
        created_at="2026-08-17T10:00:00+00:00",
        leveling_score=35.0,
        leveling_level="DEVELOPING",
        leveling_trend="IMPROVING",
        consistency_score=31.5,
        consistency_trend="STABLE",
    )

    timelines = SkillProgressTimelineService.build(
        snapshots=[s1, s2, s3]
    )

    summary = OverallPlayerDevelopmentService.summarize(
        timelines=timelines,
        primary_skill_id="leveling",
    )

    result = ProgressIntelligenceService.build(
        snapshots=[s1, s2, s3],
        primary_skill_id="leveling",
    )

    leveling_points = timelines["leveling"]
    economy_points = timelines["economy"]

    checks = [
        ("12.4 cria timeline por Skill", set(timelines) == {"leveling", "consistency", "economy"}),
        ("12.4 preserva 3 snapshots", len(leveling_points) == 3),
        ("12.4 preserva ordem", leveling_points[0].snapshot_id == "s1" and leveling_points[-1].snapshot_id == "s3"),
        ("12.4 preserva score inicial", leveling_points[0].score == 15.0),
        ("12.4 preserva score atual", leveling_points[-1].score == 35.0),
        ("12.4 Economy segue sem score", all(item.score is None for item in economy_points)),
        ("12.5 detecta Improving", summary.status == "IMPROVING"),
        ("12.5 confiança é pelo conjunto observado", summary.confidence in {"MODERATE", "HIGH"}),
        ("12.5 preserva Skill prioritária", summary.primary_skill_id == "leveling"),
        ("12.5 não usa média simples", "não é uma média simples" in summary.rationale),
        ("12.6 gera insights", len(result["insights"]) >= 1),
        ("12.6 detecta avanço acumulado", any(item["role"] == "progress" for item in result["insights"])),
        ("12.6 detecta mudança de nível", any(item["role"] == "milestone" for item in result["insights"])),
        ("12.6 insight usa delta real", any(item["evidence"].get("delta") == 20.0 for item in result["insights"] if "delta" in item["evidence"])),
        ("12.6 não altera prioridade", result["overall_development"]["primary_skill_id"] == "leveling"),
        ("Payload possui timelines", "timelines" in result),
        ("Payload possui overall_development", "overall_development" in result),
        ("Payload possui insights", "insights" in result),
    ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 12.4 A 12.6 - PROGRESS INTELLIGENCE V1")
    print("=" * 82)

    passed = 0
    for index, (name, ok) in enumerate(checks, start=1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("FASE 12.4-12.6 PROGRESS INTELLIGENCE V1: VALIDADO")
        raise SystemExit(0)

    print("FASE 12.4-12.6 PROGRESS INTELLIGENCE V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
