from __future__ import annotations

from src.performance_engine.calculators.combat_availability import (
    CombatAvailabilityChecker,
)
from src.performance_engine.calculators.combat_metrics_calculator import (
    CombatMetricsCalculator,
)
from src.performance_engine.models import Match


def build_match(
    index: int,
    *,
    damage: int,
    eliminated: int,
    placement: int = 4,
) -> Match:
    return Match(
        match_id=f"TEST_{index}",
        placement=placement,
        level=8,
        gold_left=10,
        last_round=30,
        players_eliminated=eliminated,
        total_damage_to_players=damage,
        time_eliminated=1800.0,
    )


def main() -> None:
    print("=" * 80)
    print("TESTE - COMBAT AVAILABILITY LAYER")
    print("=" * 80)

    all_zero = [
        build_match(
            i,
            damage=0,
            eliminated=0,
        )
        for i in range(1, 6)
    ]

    availability = CombatAvailabilityChecker.evaluate(
        all_zero
    )
    metrics = CombatMetricsCalculator.calculate(
        all_zero
    )

    assert availability.available is False
    assert metrics.average_damage_to_players is None
    assert metrics.average_players_eliminated is None

    print("[OK] 5/5 zero -> combate indisponível")

    isolated_zero = [
        build_match(1, damage=0, eliminated=0),
        build_match(2, damage=85, eliminated=1),
        build_match(3, damage=100, eliminated=2),
        build_match(4, damage=74, eliminated=1),
        build_match(5, damage=121, eliminated=2),
    ]

    availability = CombatAvailabilityChecker.evaluate(
        isolated_zero
    )
    metrics = CombatMetricsCalculator.calculate(
        isolated_zero
    )

    assert availability.available is True
    assert metrics.average_damage_to_players is not None
    assert metrics.average_players_eliminated is not None

    print("[OK] 1/5 zero -> combate continua válido")
    print(
        "[INFO] damage médio:",
        metrics.average_damage_to_players,
    )
    print(
        "[INFO] eliminações médias:",
        metrics.average_players_eliminated,
    )

    four_of_five_zero = [
        build_match(
            i,
            damage=0,
            eliminated=0,
        )
        for i in range(1, 5)
    ] + [
        build_match(
            5,
            damage=90,
            eliminated=1,
        )
    ]

    availability = CombatAvailabilityChecker.evaluate(
        four_of_five_zero
    )

    assert availability.available is False
    assert round(
        availability.suspicious_ratio,
        2,
    ) == 0.80

    print("[OK] 4/5 zero -> limite de 80% bloqueia combate")

    print("=" * 80)
    print("TODOS OS TESTES PASSARAM")
    print("=" * 80)


if __name__ == "__main__":
    main()
