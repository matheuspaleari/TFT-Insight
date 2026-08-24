
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.composition_intelligence_v2.services.composition_player_presenter import (
    CompositionPlayerPresenter,
)


@dataclass
class Profile:
    composition_key: str
    carry_character_id: str
    tank_character_id: str
    primary_trait_names: tuple
    core_unit_ids: tuple
    matches_played: int
    usage_rate: float
    average_placement: float
    top4_rate: float
    win_rate: float
    average_contest_score: float | None
    confidence_score: float
    confidence_level: str
    recommendation_score: float
    recommendation_label: str


class Report:
    matches_analyzed = 30
    unique_compositions = 19
    diversity_rate = 63.33
    repetition_rate = 10.0
    repetition_signal = "ALTA_DIVERSIDADE"
    repetition_interpretation = (
        "Nenhuma estrutura domina fortemente o histórico recente."
    )
    limitations = (
        "Board final não reconstrói transições.",
    )

    profiles = (
        Profile(
            "composition_11",
            "TFT17_Kindred",
            "TFT17_Maokai",
            ("TFT17_DRX",),
            ("TFT17_Kindred", "TFT17_Maokai"),
            3,
            10.0,
            3.33,
            100.0,
            0.0,
            40.0,
            28.11,
            "Baixa",
            50.0,
            "Amostra insuficiente",
        ),
        Profile(
            "composition_2",
            "TFT17_AurelionSol",
            "TFT17_Tank",
            ("TFT17_Trait",),
            ("TFT17_AurelionSol",),
            2,
            6.67,
            2.0,
            100.0,
            50.0,
            30.0,
            20.0,
            "Exploratória",
            55.0,
            "Exploratória",
        ),
    )

    most_used = profiles[0]
    best_supported = profiles[0]


payload = CompositionPlayerPresenter.build(
    Report()
)

checks = [
    (
        "Resumo público existe",
        payload["summary"]["matches_analyzed"] == 30,
    ),
    (
        "Composições públicas existem",
        len(payload["compositions"]) == 2,
    ),
    (
        "Support removido",
        "support_character_id"
        not in payload["compositions"][0],
    ),
    (
        "Elegibilidade separada",
        payload["compositions"][0][
            "eligible_for_comparison"
        ] is True,
    ),
    (
        "2 partidas não elegível",
        payload["compositions"][1][
            "eligible_for_comparison"
        ] is False,
    ),
    (
        "Confiança permanece separada",
        payload["compositions"][0][
            "statistical_confidence"
        ]["level"] == "Baixa",
    ),
    (
        "Coach não promete melhor escolha",
        "não prova"
        in " ".join(
            payload["coach"]["observations"]
        ),
    ),
    (
        "Guardrail de force",
        any(
            "não prova intenção"
            in item
            for item in payload["coach"]["guardrails"]
        ),
    ),
]

print("=" * 100)
print("#25 - FINALIZAÇÃO COACH / API / UI CONTRACT")
print("=" * 100)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{i}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#25 FINALIZAÇÃO: VALIDADA")
else:
    raise SystemExit(1)
