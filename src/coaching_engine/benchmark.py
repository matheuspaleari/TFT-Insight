from dataclasses import dataclass
from statistics import mean


@dataclass(slots=True, frozen=True)
class BenchmarkComparison:
    metric: str
    player_value: float
    challenger_value: float
    difference: float
    percentile_estimate: float
    label: str


class ChallengerBenchmarkEngine:
    METRICS = (
        "top4_rate",
        "win_rate",
        "average_placement",
        "average_level",
        "level_8_rate",
        "level_9_rate",
        "average_damage",
    )

    @classmethod
    def build_metrics(cls, *, matches: list) -> dict:
        if not matches:
            raise ValueError("matches vazio.")

        total = len(matches)

        return {
            "sample_size": total,
            "top4_rate": (
                sum(match.placement <= 4 for match in matches)
                / total * 100.0
            ),
            "win_rate": (
                sum(match.placement == 1 for match in matches)
                / total * 100.0
            ),
            "average_placement": mean(
                match.placement for match in matches
            ),
            "average_level": mean(
                match.level for match in matches
            ),
            "level_8_rate": (
                sum(match.level >= 8 for match in matches)
                / total * 100.0
            ),
            "level_9_rate": (
                sum(match.level >= 9 for match in matches)
                / total * 100.0
            ),
            "average_damage": mean(
                match.total_damage_to_players
                for match in matches
            ),
        }

    @classmethod
    def compare(
        cls,
        *,
        player_metrics: dict,
        challenger_metrics: dict,
    ) -> tuple[BenchmarkComparison, ...]:
        output = []

        for metric in cls.METRICS:
            if metric not in player_metrics or metric not in challenger_metrics:
                continue

            player = float(player_metrics[metric])
            benchmark = float(challenger_metrics[metric])
            difference = player - benchmark

            effective = (
                -difference
                if metric == "average_placement"
                else difference
            )

            deviation = max(abs(benchmark) * 0.15, 1.0)
            percentile = max(
                1.0,
                min(99.0, 50.0 + effective / deviation * 18.0),
            )

            if effective >= deviation:
                label = "Acima do Challenger"
            elif effective <= -deviation:
                label = "Abaixo do Challenger"
            else:
                label = "Próximo da média Challenger"

            output.append(
                BenchmarkComparison(
                    metric=metric,
                    player_value=round(player, 2),
                    challenger_value=round(benchmark, 2),
                    difference=round(difference, 2),
                    percentile_estimate=round(percentile, 2),
                    label=label,
                )
            )

        return tuple(output)
