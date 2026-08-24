from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.progress_aware_coach import ProgressAwareCoachService


def progress(scores):
    return {
        "timelines": {
            "leveling": [
                {"score": score, "level": "BEGINNER"}
                for score in scores
            ]
        }
    }


def coach(scores):
    return ProgressAwareCoachService.build(
        progress=progress(scores),
        priority_skill_id="leveling",
        adaptive_strategy={
            "current_task_id": "plan_level_before_spending",
            "current_difficulty": "FOUNDATION",
        },
    )


def main():
    checks = []

    # Cenário real atual: uma única queda entre dois snapshots.
    current = coach([15.22, 3.08])
    c = current["context"]
    s = current["strategy"]
    a = current["adaptation"]
    e = current["explanation"]

    checks += [
        ("Histórico curto gera WATCH", c["signal"] == "WATCH"),
        ("Histórico curto mantém LOW", c["confidence"] == "LOW"),
        ("Queda real preserva delta -12.14", abs(c["delta"] + 12.14) < 0.001),
        ("WATCH não reage automaticamente", not c["enough_for_reaction"]),
        ("WATCH gera OBSERVE", s["action"] == "OBSERVE"),
        ("OBSERVE gera KEEP_AND_OBSERVE", a["mode"] == "KEEP_AND_OBSERVE"),
        ("Prioridade continua leveling", s["priority_skill_id"] == "leveling"),
        ("Task atual é preservada", a["task_id"] == "plan_level_before_spending"),
        ("Difficulty FOUNDATION é preservada", a["difficulty"] == "FOUNDATION"),
        ("Não altera missão", not a["changes_mission"]),
        ("Não altera prioridade", not a["changes_priority"]),
        ("Não altera dificuldade", not a["changes_difficulty"]),
        ("Explicação possui próximo passo", bool(e["next_step"])),
        ("Explicação é determinística", e["source"] == "deterministic"),
    ]

    # Queda persistente.
    regression = coach([15.22, 10.00, 3.08])
    rc = regression["context"]
    rs = regression["strategy"]
    ra = regression["adaptation"]
    checks += [
        ("Queda persistente gera REGRESSION", rc["signal"] == "REGRESSION"),
        ("REGRESSION tem reação", rc["enough_for_reaction"]),
        ("REGRESSION reforça fundamentos", rs["action"] == "REINFORCE_FOUNDATION"),
        ("Adaptação vira REINFORCE", ra["mode"] == "REINFORCE"),
        ("Regressão não troca prioridade", rs["priority_skill_id"] == "leveling"),
        ("Regressão não troca difficulty sozinha", not ra["changes_difficulty"]),
    ]

    # Melhora persistente.
    improvement = coach([3.08, 9.40, 17.20])
    ic = improvement["context"]
    ins = improvement["strategy"]
    ia = improvement["adaptation"]
    checks += [
        ("Melhora persistente gera IMPROVEMENT", ic["signal"] == "IMPROVEMENT"),
        ("IMPROVEMENT tem reação", ic["enough_for_reaction"]),
        ("Melhora prepara avanço", ins["action"] == "RECOGNIZE_AND_PREPARE_ADVANCE"),
        ("Adaptação prepara progressão", ia["mode"] == "PREPARE_PROGRESSION"),
        ("Melhora não avança difficulty sozinha", not ia["changes_difficulty"]),
    ]

    # Evidência mais forte.
    strong = coach([3.08, 9.40, 17.20, 26.00])
    checks += [
        ("4 snapshots consistentes chegam a HIGH", strong["context"]["confidence"] == "HIGH"),
        ("HIGH continua sem trocar Skill", strong["strategy"]["priority_skill_id"] == "leveling"),
    ]

    # Histórico misto.
    mixed = coach([10.0, 11.0, 10.2, 10.8])
    checks += [
        ("Oscilação gera STABLE_OR_MIXED", mixed["context"]["signal"] == "STABLE_OR_MIXED"),
        ("Oscilação mantém abordagem", mixed["strategy"]["action"] == "MAINTAIN"),
        ("Oscilação não reage", not mixed["context"]["enough_for_reaction"]),
    ]

    # Integração física da 13.7.
    page = (ROOT / "partner_platform/pages/benchmark_page.py").read_text(encoding="utf-8")
    route = (ROOT / "src/integration_engine/api/routes/benchmark.py").read_text(encoding="utf-8")
    contract = (ROOT / "src/integration_engine/contracts/benchmark.py").read_text(encoding="utf-8")

    checks += [
        ("API expõe progress_aware_coach", 'comparison_data["progress_aware_coach"]' in route),
        ("Contrato preserva progress_aware_coach", "progress_aware_coach: BenchmarkProgressAwareCoach" in contract),
        ("UI consome progress_aware_coach", 'comparison.get("progress_aware_coach")' in page),
        ("UI contém seção longitudinal", "Coach acompanhando sua evolução" in page),
        ("UI mantém Progress Dashboard", "Sua evolução" in page),
        ("UI mantém Adaptive Coach", "Inteligência adaptativa do coach" in page),
    ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 13.8 - END-TO-END FINAL V1")
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
        print("FASE 13 END-TO-END V1: VALIDADA")
        raise SystemExit(0)

    print("FASE 13 END-TO-END V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
