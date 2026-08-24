from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.services.training_metric_resolver import TrainingMetricResolver


def main() -> None:
    metrics = SimpleNamespace(
        general=SimpleNamespace(
            average_level=8.25,
        ),
        combat=SimpleNamespace(
            average_damage_to_players=101.5,
            average_players_eliminated=1.25,
        ),
        consistency=SimpleNamespace(
            placement_standard_deviation=2.1,
        ),
        economy=SimpleNamespace(
            average_gold_left=14.0,
        ),
    )

    checks = [
        (
            "average_level resolve em general",
            TrainingMetricResolver.resolve(
                player_metrics=metrics,
                metric_id="average_level",
            ) == 8.25,
        ),
        (
            "average_damage resolve em combat",
            TrainingMetricResolver.resolve(
                player_metrics=metrics,
                metric_id="average_damage_to_players",
            ) == 101.5,
        ),
        (
            "average_players_eliminated resolve em combat",
            TrainingMetricResolver.resolve(
                player_metrics=metrics,
                metric_id="average_players_eliminated",
            ) == 1.25,
        ),
        (
            "placement_standard_deviation resolve em consistency",
            TrainingMetricResolver.resolve(
                player_metrics=metrics,
                metric_id="placement_standard_deviation",
            ) == 2.1,
        ),
        (
            "average_gold_left resolve em economy",
            TrainingMetricResolver.resolve(
                player_metrics=metrics,
                metric_id="average_gold_left",
            ) == 14.0,
        ),
        (
            "métrica desconhecida não inventa valor",
            TrainingMetricResolver.resolve(
                player_metrics=metrics,
                metric_id="unknown_metric",
            ) is None,
        ),
        (
            "delta positivo",
            TrainingMetricResolver.delta(
                before=8.0,
                after=8.4,
            ) == 0.4,
        ),
        (
            "delta negativo",
            TrainingMetricResolver.delta(
                before=100.0,
                after=80.0,
            ) == -20.0,
        ),
        (
            "delta ausente permanece inconclusivo",
            TrainingMetricResolver.delta(
                before=None,
                after=8.0,
            ) is None,
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - TRAINING METRIC RESOLVER V1.1")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("TRAINING METRIC RESOLVER V1.1: VALIDADO")
        raise SystemExit(0)

    print("TRAINING METRIC RESOLVER V1.1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
