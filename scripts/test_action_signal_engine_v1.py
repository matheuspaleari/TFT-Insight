from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.action_signal import ActionSignalEngine


@dataclass
class SignalEnum:
    value: str


@dataclass
class HistoricalMetric:
    metric_id: str
    signal: SignalEnum


@dataclass
class HistoricalContext:
    metrics: tuple


@dataclass
class Section:
    section_id: str
    text: str


@dataclass
class Report:
    supporting_sections: tuple


def main() -> None:
    historical = HistoricalContext(
        metrics=(
            HistoricalMetric(
                "level",
                SignalEnum("WORSENING"),
            ),
            HistoricalMetric(
                "total_damage_to_players",
                SignalEnum("IMPROVING"),
            ),
        )
    )

    report = Report(
        supporting_sections=(
            Section(
                "match_board_pressure",
                "Pressão abaixo do padrão recente.",
            ),
            Section(
                "match_placement",
                "Resultado abaixo do padrão.",
            ),
        )
    )

    result = ActionSignalEngine.build(
        post_match_report=report,
        post_match_analysis=object(),
        historical_context=historical,
        active_skill_id="leveling",
        active_skill_label="Leveling",
        mission_title="Planejar o próximo nível",
    )

    public = " ".join(
        [
            result.summary,
            result.primary.title if result.primary else "",
            result.primary.action if result.primary else "",
            result.primary.reason if result.primary else "",
            *[
                x.title + " " + x.action + " " + x.reason
                for x in result.secondary
            ],
            *[
                x.title + " " + x.action + " " + x.reason
                for x in result.watch
            ],
        ]
    )

    checks = [
        ("Cria prioridade principal", result.primary is not None),
        ("Prioriza Leveling", result.primary.skill_id == "leveling"),
        ("Ação é de planejamento", "Planeje" in result.primary.title),
        ("Não afirma causalidade", "não prova" in result.primary.reason.lower()),
        ("No máximo 2 secundários", len(result.secondary) <= 2),
        ("No máximo 2 watch", len(result.watch) <= 2),
        ("Pressão vira apoio", any(x.signal_id == "board_pressure_check" for x in result.secondary)),
        ("Resultado isolado vira watch", any(x.signal_id == "result_is_context" for x in result.watch)),
        ("Não expõe WORSENING", "WORSENING" not in public),
        ("Não expõe PRIMARY", "PRIMARY" not in public),
        ("Não troca prioridade", result.changes_learning_priority is False),
        ("Não troca missão", result.changes_mission is False),
        ("Não troca dificuldade", result.changes_difficulty is False),
        ("Não muda EvidenceClass", result.changes_evidence_class is False),
        ("Não conta como missão", result.counts_as_mission_evidence is False),
        ("Não prevê rank up", result.predicts_rank_up is False),
    ]

    print("=" * 92)
    print("TFT INSIGHT - ACTION SIGNAL ENGINE V1")
    print("=" * 92)

    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 92)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("ACTION SIGNAL ENGINE V1: VALIDADO")
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
