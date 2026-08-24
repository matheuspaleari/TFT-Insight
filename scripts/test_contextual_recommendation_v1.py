from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contextual_recommendation import (
    ContextualRecommendationEngine,
)


@dataclass
class Action:
    title: str
    action: str
    reason: str


@dataclass
class ActionReport:
    primary: Action
    secondary: tuple


def main() -> None:
    actions = ActionReport(
        primary=Action(
            title="Planeje a próxima subida antes de gastar",
            action=(
                "Antes de comprar experiência, defina qual nível você quer "
                "alcançar e qual condição faria você estabilizar antes."
            ),
            reason=(
                "Seu nível final médio vem terminando mais baixo no bloco recente. "
                "Isso não prova piora de decisão."
            ),
        ),
        secondary=(
            Action(
                title="Cheque pressão",
                action=(
                    "Compare se seu board está preservando vida e "
                    "convertendo força em pressão."
                ),
                reason="Pressão abaixo do padrão.",
            ),
        ),
    )

    competitive = {
        "group_label": "Avançado BR",
        "spectrum_band": "Entrada",
    }

    fusion = {
        "problem_observed": (
            "Leveling é a principal oportunidade de treino"
        ),
        "training_focus": "Planejar o próximo nível",
        "strength_to_preserve": "Economia",
    }

    result = ContextualRecommendationEngine.build(
        action_signals=actions,
        competitive_context=competitive,
        coach_fusion=fusion,
        active_skill_label="Leveling",
        mission_title="Planejar o próximo nível",
    )

    public = " ".join(
        [
            result.title,
            result.recommendation,
            result.why_now,
            result.competitive_context,
            result.training_context,
            result.preserve or "",
            *result.secondary_actions,
        ]
    )

    checks = [
        ("Cria recomendação", bool(result.recommendation)),
        ("Mantém ação principal", "Antes de comprar experiência" in result.recommendation),
        ("Usa grupo competitivo", "Avançado BR" in result.recommendation),
        ("Usa faixa do espectro", "Entrada" in result.recommendation),
        ("Não trata grupo como requisito", "não como requisito de promoção" in result.recommendation),
        ("Mantém missão", "Planejar o próximo nível" in result.recommendation),
        ("Usa Coach Fusion", "Leveling é a principal oportunidade" in result.why_now),
        ("Usa foco operacional", "foco operacional atual" in result.why_now),
        ("Preserva força", result.preserve == "Economia"),
        ("Leva apoio secundário", len(result.secondary_actions) == 1),
        ("Não expõe PRIMARY", "PRIMARY" not in public),
        ("Não prevê promoção", "você vai subir" not in public.lower()),
        ("Não muda prioridade", result.changes_learning_priority is False),
        ("Não muda missão", result.changes_mission is False),
        ("Não muda dificuldade", result.changes_difficulty is False),
        ("Não muda EvidenceClass", result.changes_evidence_class is False),
        ("Não conta como missão", result.counts_as_mission_evidence is False),
        ("Não prevê rank up", result.predicts_rank_up is False),
    ]

    print("=" * 96)
    print("TFT INSIGHT - CONTEXTUAL RECOMMENDATION V1")
    print("=" * 96)

    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 96)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("CONTEXTUAL RECOMMENDATION V1: VALIDADO")
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
