from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.services.training_cycle_evaluation_engine import (
    TrainingCycleEvaluationEngine,
)


def evaluate(before, after, after_n=5):
    return TrainingCycleEvaluationEngine.evaluate(
        before_metrics=before,
        after_metrics=after,
        before_coverage=96.67,
        after_coverage=100.0,
        before_sample_size=29,
        after_sample_size=after_n,
    )


def main() -> None:
    real_before = {
        "average_level": 8.38,
        "average_damage_to_players": 108.79,
        "average_players_eliminated": 1.24,
    }
    real_after = {
        "average_level": 7.80,
        "average_damage_to_players": 88.40,
        "average_players_eliminated": 0.60,
    }

    real = evaluate(
        real_before,
        real_after,
        after_n=5,
    )

    positive = evaluate(
        {
            "average_level": 7.5,
            "average_damage_to_players": 80.0,
            "average_players_eliminated": 0.8,
        },
        {
            "average_level": 8.0,
            "average_damage_to_players": 100.0,
            "average_players_eliminated": 1.2,
        },
    )

    stable = evaluate(
        {
            "average_level": 8.0,
            "average_damage_to_players": 100.0,
            "average_players_eliminated": 1.0,
        },
        {
            "average_level": 8.1,
            "average_damage_to_players": 102.0,
            "average_players_eliminated": 1.02,
        },
    )

    mixed = evaluate(
        {
            "average_level": 8.0,
            "average_damage_to_players": 100.0,
            "average_players_eliminated": 1.0,
        },
        {
            "average_level": 8.5,
            "average_damage_to_players": 80.0,
            "average_players_eliminated": 1.0,
        },
    )

    tiny_sample = evaluate(
        real_before,
        real_after,
        after_n=2,
    )

    nine_games = evaluate(
        real_before,
        real_after,
        after_n=9,
    )

    ten_games = evaluate(
        real_before,
        real_after,
        after_n=10,
    )

    checks = [
        (
            "Ciclo real é NEGATIVE",
            real.result == "NEGATIVE",
        ),
        (
            "Ciclo real tem 3 sinais negativos",
            real.negative_metrics == 3,
        ),
        (
            "5 partidas recebem confiança MODERATE",
            real.confidence == "MODERATE",
        ),
        (
            "5 partidas não passam do teto de 69.99",
            real.confidence_score <= 69.99,
        ),
        (
            "Cenário positivo é POSITIVE",
            positive.result == "POSITIVE",
        ),
        (
            "Variações pequenas são STABLE",
            stable.result == "STABLE",
        ),
        (
            "Sinais mistos são INCONCLUSIVE",
            mixed.result == "INCONCLUSIVE",
        ),
        (
            "AFTER com menos de 3 jogos é INCONCLUSIVE",
            tiny_sample.result == "INCONCLUSIVE",
        ),
        (
            "9 partidas ainda não recebem HIGH",
            nine_games.confidence != "HIGH",
        ),
        (
            "10 partidas podem receber HIGH",
            ten_games.confidence == "HIGH",
        ),
        (
            "Conclusão não afirma causalidade",
            "Não prova" in real.caveat,
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - TRAINING CYCLE EVALUATION ENGINE V1.1")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("-" * 82)
    print("CASO REAL ESPERADO")
    print("-" * 82)
    print(f"Resultado  : {real.result}")
    print(
        f"Confiança  : {real.confidence} "
        f"({real.confidence_score:.2f}%)"
    )
    print(
        "Sinais     : "
        f"+{real.positive_metrics} / "
        f"={real.stable_metrics} / "
        f"-{real.negative_metrics}"
    )
    print(f"Motivo     : {real.reason}")
    print(f"Limitação  : {real.caveat}")

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print(
            "TRAINING CYCLE EVALUATION ENGINE V1.1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "TRAINING CYCLE EVALUATION ENGINE V1.1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
