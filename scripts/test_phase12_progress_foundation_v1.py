from __future__ import annotations

import tempfile
from pathlib import Path

from src.progress_intelligence import (
    ProgressHistoryService,
    ProgressMilestoneService,
    ProgressSnapshotService,
)


def profile(
    *,
    score: float,
    level: str,
    trend: str,
    difficulty: str,
):
    return {
        "current_priority_skill_id": "leveling",
        "skills": {
            "leveling": {
                "state": "IN_TRAINING",
                "score": score,
                "level": level,
                "trend": trend,
                "trend_confidence": "MODERATE",
                "cycles_total": 2,
                "conclusive_cycles": 2,
                "current_difficulty": difficulty,
            },
            "economy": {
                "state": "OBSERVED",
                "score": None,
                "level": "NOT_EVALUATED",
                "trend": "INSUFFICIENT_HISTORY",
                "trend_confidence": "LOW",
                "cycles_total": 0,
                "conclusive_cycles": 0,
                "current_difficulty": None,
            },
        },
    }


def main():
    before = ProgressSnapshotService.build(
        learning_profile=profile(
            score=15.22,
            level="BEGINNER",
            trend="INSUFFICIENT_HISTORY",
            difficulty="FOUNDATION",
        ),
        archived_cycles_total=2,
        created_at="2026-08-17T10:00:00+00:00",
    )
    after = ProgressSnapshotService.build(
        learning_profile=profile(
            score=35.0,
            level="DEVELOPING",
            trend="IMPROVING",
            difficulty="INTERMEDIATE",
        ),
        archived_cycles_total=4,
        created_at="2026-08-24T10:00:00+00:00",
    )

    milestones = ProgressMilestoneService.detect(
        previous=before,
        current=after,
    )

    with tempfile.TemporaryDirectory() as temp:
        player_dir = Path(temp) / "player"
        first = ProgressHistoryService.append(
            player_directory=player_dir,
            snapshot=before,
        )
        duplicate = ProgressHistoryService.append(
            player_directory=player_dir,
            snapshot=before,
        )
        second = ProgressHistoryService.append(
            player_directory=player_dir,
            snapshot=after,
        )
        loaded = ProgressHistoryService.load(
            player_directory=player_dir
        )

    types = {item.milestone_type for item in milestones}

    checks = [
        ("Snapshot preserva prioridade", before.priority_skill_id == "leveling"),
        ("Snapshot preserva score", before.skills["leveling"]["score"] == 15.22),
        ("Economy não inventa score", before.skills["economy"]["score"] is None),
        ("Primeiro snapshot é persistido", first is True),
        ("Snapshot duplicado não é persistido", duplicate is False),
        ("Segundo snapshot é persistido", second is True),
        ("Histórico é append-only", len(loaded) == 2),
        ("Ordem histórica é preservada", loaded[0].snapshot_id == before.snapshot_id),
        ("LEVEL_UP detectado", "LEVEL_UP" in types),
        ("IMPROVING_TREND detectado", "IMPROVING_TREND" in types),
        ("DIFFICULTY_UP detectado", "DIFFICULTY_UP" in types),
        ("Milestones não alteram prioridade", after.priority_skill_id == "leveling"),
        ("Score histórico permanece imutável", loaded[0].skills["leveling"]["score"] == 15.22),
        ("Score novo permanece separado", loaded[1].skills["leveling"]["score"] == 35.0),
        ("Sem baseline não cria milestone", ProgressMilestoneService.detect(previous=None, current=before) == []),
    ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 12.1 A 12.3 - PROGRESS FOUNDATION V1")
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
        print("FASE 12.1-12.3 PROGRESS FOUNDATION V1: VALIDADO")
        raise SystemExit(0)

    print("FASE 12.1-12.3 PROGRESS FOUNDATION V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
