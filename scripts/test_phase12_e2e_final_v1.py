from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.progress_intelligence.services.progress_history_service import ProgressHistoryService
from src.progress_intelligence.services.progress_intelligence_service import ProgressIntelligenceService
from src.progress_intelligence.services.progress_milestone_service import ProgressMilestoneService
from src.progress_intelligence.services.progress_snapshot_service import ProgressSnapshotService


def make_profile(leveling_score, board_score, board_level):
    return {
        "priority_skill_id": "leveling",
        "skills": {
            "leveling": {
                "score": leveling_score, "level": "BEGINNER",
                "trend": "INSUFFICIENT_HISTORY", "trend_confidence": "LOW",
                "cycles_total": 2, "conclusive_cycles": 1,
                "current_difficulty": "FOUNDATION",
            },
            "consistency": {
                "score": 29.40, "level": "DEVELOPING",
                "trend": "INSUFFICIENT_HISTORY", "trend_confidence": "LOW",
                "cycles_total": 1, "conclusive_cycles": 0,
                "current_difficulty": None,
            },
            "board_pressure": {
                "score": board_score, "level": board_level,
                "trend": "INSUFFICIENT_HISTORY", "trend_confidence": "LOW",
                "cycles_total": 0, "conclusive_cycles": 0,
                "current_difficulty": None,
            },
            "economy": {
                "score": None, "level": "NOT_EVALUATED",
                "trend": "INSUFFICIENT_HISTORY", "trend_confidence": "LOW",
                "cycles_total": 0, "conclusive_cycles": 0,
                "current_difficulty": None,
            },
        },
    }


def main():
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        player_dir = Path(tmp) / "player"

        s1 = ProgressSnapshotService.build(
            learning_profile=make_profile(15.22, 48.31, "COMPETENT"),
            archived_cycles_total=2,
            metadata={"source": "phase12_e2e"},
        )
        ProgressHistoryService.append(player_directory=player_dir, snapshot=s1)
        h1 = ProgressHistoryService.load(player_directory=player_dir)

        s2 = ProgressSnapshotService.build(
            learning_profile=make_profile(3.08, 69.23, "ADVANCED"),
            archived_cycles_total=2,
            metadata={"source": "phase12_e2e"},
        )
        milestones = ProgressMilestoneService.detect(previous=h1[-1], current=s2)
        ProgressHistoryService.append(player_directory=player_dir, snapshot=s2)
        history = ProgressHistoryService.load(player_directory=player_dir)

        intel = ProgressIntelligenceService.build(
            snapshots=history, primary_skill_id="leveling"
        )
        timelines = intel["timelines"]
        overall = intel["overall_development"]
        insights = intel["insights"]
        leveling = timelines["leveling"]
        board = timelines["board_pressure"]
        economy = timelines["economy"]

        checks = [
            ("12.1 snapshot inicial criado", len(h1) == 1),
            ("12.2 segundo snapshot persistido", len(history) == 2),
            ("12.3 milestones processados", isinstance(milestones, list)),
            ("12.4 timeline possui 4 Skills", len(timelines) == 4),
            ("12.4 Leveling possui 2 pontos", len(leveling) == 2),
            ("12.4 score inicial 15.22", abs(leveling[0]["score"] - 15.22) < .001),
            ("12.4 score atual 3.08", abs(leveling[-1]["score"] - 3.08) < .001),
            ("12.4 delta Leveling -12.14", abs((leveling[-1]["score"] - leveling[0]["score"]) + 12.14) < .001),
            ("Skills evoluem independentemente", board[0]["score"] < board[-1]["score"]),
            ("Economy permanece None", all(x["score"] is None for x in economy)),
            ("12.5 overall conservador", overall["status"] == "INSUFFICIENT_HISTORY"),
            ("12.5 confiança LOW", overall["confidence"] == "LOW"),
            ("Prioridade permanece Leveling", overall["primary_skill_id"] == "leveling"),
            ("12.6 possui insight", len(insights) >= 1),
            ("12.6 detecta queda", any(x["role"] == "attention" for x in insights)),
            ("12.6 delta do insight -12.14", any(abs(x.get("evidence", {}).get("delta", 999) + 12.14) < .001 for x in insights)),
            ("Não existe score geral artificial", "score" not in overall),
            ("Não altera missão", "mission" not in intel),
            ("Não escolhe outra prioridade", overall["primary_skill_id"] == "leveling"),
            ("Histórico insuficiente não vira melhora", overall["status"] != "IMPROVING"),
            ("Histórico insuficiente não vira regressão global", overall["status"] != "NEEDS_ATTENTION"),
            ("Timeline mantém Consistency", "consistency" in timelines),
            ("Timeline mantém Board Pressure", "board_pressure" in timelines),
            ("Timeline mantém Economy", "economy" in timelines),
            ("Payload final possui insights", "insights" in intel),
        ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 12.8 - END-TO-END FINAL V1")
    print("=" * 82)
    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
    print("\n" + "=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed == len(checks):
        print("FASE 12 END-TO-END V1: VALIDADA")
        raise SystemExit(0)
    print("FASE 12 END-TO-END V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
