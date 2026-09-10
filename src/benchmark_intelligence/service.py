from __future__ import annotations

import csv
from dataclasses import asdict
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

from src.performance_engine.calculators import (
    PlayerMetricsCalculator,
)


class BenchmarkIntelligenceService:
    """
    Constrói o Benchmark Intelligence usando dados locais já coletados.

    Fontes:
    - data/analysis/challenger_metrics.csv
    - data/role_inference/challenger/matches/*.json

    O catálogo de nomes é persistido em:
    - data/benchmark/challenger_player_catalog.json

    A construção do catálogo não faz chamadas à Riot API. Os Riot IDs
    são extraídos dos payloads de partidas já armazenados em cache.
    """

    METRICS = {
        "top4_rate": {
            "label": "Top 4",
            "higher_is_better": True,
        },
        "win_rate": {
            "label": "Win rate",
            "higher_is_better": True,
        },
        "average_placement": {
            "label": "Average placement",
            "higher_is_better": False,
        },
        "average_level": {
            "label": "Average level",
            "higher_is_better": True,
        },
        "average_damage_to_players": {
            "label": "Damage",
            "higher_is_better": True,
        },
        "placement_standard_deviation": {
            "label": "Consistency",
            "higher_is_better": False,
        },
    }

    def __init__(
        self,
        *,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(project_root)
        self.metrics_path = (
            self.project_root
            / "data"
            / "analysis"
            / "challenger_metrics.csv"
        )
        self.matches_dir = (
            self.project_root
            / "data"
            / "role_inference"
            / "challenger"
            / "matches"
        )
        self.catalog_path = (
            self.project_root
            / "data"
            / "benchmark"
            / "challenger_player_catalog.json"
        )

    def overview(
        self,
        *,
        include_players: bool = True,
    ) -> dict[str, Any]:
        rows = self._load_rows()

        players = (
            self._build_players(rows)
            if include_players
            else []
        )

        matches_analyzed = sum(
            int(float(row["matches_played"]))
            for row in rows
        )

        return {
            "benchmark_id": "challenger_br",
            "name": "Challenger BR",
            "players_analyzed": len(rows),
            "matches_analyzed": matches_analyzed,
            "metrics": self._aggregate_metrics(rows),
            "players": players,
            "catalog_source": (
                "local_match_cache"
                if players
                else "not_loaded"
            ),
        }

    def compare_matches(
        self,
        *,
        matches: list,
        player_puuid: str,
    ) -> dict[str, Any]:
        rows = self._load_rows()

        player_metrics = (
            PlayerMetricsCalculator.calculate(
                matches
            )
        )

        flat_metrics = {
            "top4_rate": (
                player_metrics.general.top4_rate
            ),
            "win_rate": (
                player_metrics.general.win_rate
            ),
            "average_placement": (
                player_metrics.general.average_placement
            ),
            "average_level": (
                player_metrics.general.average_level
            ),
            "average_damage_to_players": (
                player_metrics.combat
                .average_damage_to_players
            ),
            "placement_standard_deviation": (
                player_metrics.consistency
                .placement_standard_deviation
            ),
        }

        comparisons = []

        for metric, config in self.METRICS.items():
            player_value = flat_metrics.get(metric)

            if player_value is None:
                continue

            distribution = [
                float(row[metric])
                for row in rows
                if row.get(metric) not in {
                    None,
                    "",
                }
            ]

            if not distribution:
                continue

            benchmark_mean = mean(distribution)
            benchmark_median = median(distribution)

            percentile = self._performance_percentile(
                value=float(player_value),
                distribution=distribution,
                higher_is_better=(
                    config["higher_is_better"]
                ),
            )

            delta = (
                float(player_value)
                - benchmark_mean
            )

            effective_delta = (
                delta
                if config["higher_is_better"]
                else -delta
            )

            comparisons.append(
                {
                    "metric": metric,
                    "label": config["label"],
                    "player_value": round(
                        float(player_value),
                        2,
                    ),
                    "challenger_mean": round(
                        benchmark_mean,
                        2,
                    ),
                    "challenger_median": round(
                        benchmark_median,
                        2,
                    ),
                    "benchmark_mean": round(benchmark_mean, 2),
                    "benchmark_median": round(benchmark_median, 2),
                    "delta": round(
                        delta,
                        2,
                    ),
                    "performance_delta": round(
                        effective_delta,
                        2,
                    ),
                    "percentile": round(
                        percentile,
                        1,
                    ),
                    "assessment": (
                        self._assessment(
                            percentile
                        )
                    ),
                }
            )

        overall_percentile = (
            mean(
                item["percentile"]
                for item in comparisons
            )
            if comparisons
            else 0.0
        )

        benchmark = self.overview(
            include_players=True
        )

        return {
            "benchmark": benchmark,
            "player": {
                "puuid": player_puuid,
                "matches_analyzed": (
                    player_metrics.general
                    .matches_played
                ),
                "metrics": {
                    key: (
                        round(value, 2)
                        if value is not None
                        else None
                    )
                    for key, value
                    in flat_metrics.items()
                },
            },
            "overall_percentile": round(
                overall_percentile,
                1,
            ),
            "classification": (
                self._overall_classification(
                    overall_percentile
                )
            ),
            "comparisons": comparisons,
            "radar": [
                {
                    "metric": item["label"],
                    "player": item["percentile"],
                    "challenger_reference": 50.0,
                }
                for item in comparisons
            ],
        }

    def overview_for(
        self,
        *,
        benchmark_id: str,
        include_players: bool = True,
    ) -> dict[str, Any]:
        normalized = benchmark_id.strip().lower()
        if normalized == "challenger_br":
            return self.overview(include_players=include_players)

        data = self._load_group_benchmark(normalized)
        metrics: dict[str, dict[str, float | str]] = {}

        scalar_metrics = ("top4_rate", "win_rate", "average_placement")
        for metric in scalar_metrics:
            value = float(data[metric])
            metrics[metric] = {
                "label": self.METRICS[metric]["label"],
                "mean": value, "median": value,
                "minimum": value, "maximum": value,
                "q25": value, "q75": value,
            }

        for metric in (
            "average_level",
            "average_damage_to_players",
            "placement_standard_deviation",
        ):
            raw = data.get(metric)

            # Algumas métricas agregadas são opcionais. Ex.: benchmarks
            # construídos sem dados de combate persistem
            # average_damage_to_players como null. A ausência de uma
            # distribuição não deve invalidar o benchmark inteiro.
            if not isinstance(raw, dict):
                continue

            required_fields = (
                "mean",
                "median",
                "minimum",
                "maximum",
                "first_quartile",
                "third_quartile",
            )
            if any(raw.get(field) is None for field in required_fields):
                continue

            metrics[metric] = {
                "label": self.METRICS[metric]["label"],
                "mean": float(raw["mean"]),
                "median": float(raw["median"]),
                "minimum": float(raw["minimum"]),
                "maximum": float(raw["maximum"]),
                "q25": float(raw["first_quartile"]),
                "q75": float(raw["third_quartile"]),
            }

        return {
            "benchmark_id": normalized,
            "name": str(data["name"]),
            "players_analyzed": int(data["players_analyzed"]),
            "matches_analyzed": int(data["matches_analyzed"]),
            "metrics": metrics,
            "players": [],
            "catalog_source": "aggregate_benchmark",
        }

    def compare_matches_to(
        self,
        *,
        benchmark_id: str,
        matches: list,
        player_puuid: str,
    ) -> dict[str, Any]:
        normalized = benchmark_id.strip().lower()
        if normalized == "challenger_br":
            return self.compare_matches(matches=matches, player_puuid=player_puuid)

        overview = self.overview_for(benchmark_id=normalized, include_players=False)
        player_metrics = PlayerMetricsCalculator.calculate(matches)
        flat_metrics = {
            "top4_rate": player_metrics.general.top4_rate,
            "win_rate": player_metrics.general.win_rate,
            "average_placement": player_metrics.general.average_placement,
            "average_level": player_metrics.general.average_level,
            "average_damage_to_players": player_metrics.combat.average_damage_to_players,
            "placement_standard_deviation": player_metrics.consistency.placement_standard_deviation,
        }
        comparisons = []
        for metric, config in self.METRICS.items():
            value = flat_metrics.get(metric)
            distribution = overview["metrics"].get(metric)
            if value is None or not distribution:
                continue
            benchmark_mean = float(distribution["mean"]); benchmark_median = float(distribution["median"])
            delta = float(value) - benchmark_mean
            effective = delta if config["higher_is_better"] else -delta
            comparisons.append({
                "metric": metric, "label": config["label"],
                "player_value": round(float(value), 2),
                "challenger_mean": round(benchmark_mean, 2),
                "challenger_median": round(benchmark_median, 2),
                "benchmark_mean": round(benchmark_mean, 2),
                "benchmark_median": round(benchmark_median, 2),
                "delta": round(delta, 2), "performance_delta": round(effective, 2),
                "percentile": None,
                "assessment": "Acima da referência" if effective > 0 else ("Na referência" if effective == 0 else "Abaixo da referência"),
            })
        return {
            "benchmark": overview,
            "player": {
                "puuid": player_puuid,
                "matches_analyzed": player_metrics.general.matches_played,
                "metrics": {k: round(v, 2) if v is not None else None for k, v in flat_metrics.items()},
            },
            "overall_percentile": None,
            "classification": self._delta_classification(comparisons),
            "comparisons": comparisons,
            "radar": [],
        }

    def _load_group_benchmark(self, benchmark_id: str) -> dict[str, Any]:
        allowed = {"novice", "intermediate", "advanced", "expert", "elite"}
        if benchmark_id not in allowed:
            raise ValueError(f"Benchmark desconhecido: {benchmark_id}")
        path = self.project_root / "data" / "benchmark" / f"{benchmark_id}.json"
        if not path.exists():
            raise RuntimeError(f"Benchmark não encontrado: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _delta_classification(comparisons: list[dict[str, Any]]) -> str:
        if not comparisons:
            return "Sem dados"
        above = sum(item["performance_delta"] >= 0 for item in comparisons)
        ratio = above / len(comparisons)
        if ratio >= 0.75:
            return "Acima da referência"
        if ratio >= 0.5:
            return "Competitivo"
        return "Abaixo da referência"

    def rebuild_player_catalog(
        self,
    ) -> dict[str, dict[str, Any]]:
        rows = self._load_rows()
        target_puuids = {
            row["player"]
            for row in rows
            if row.get("player")
        }

        catalog: dict[
            str,
            dict[str, Any]
        ] = {}

        if self.matches_dir.exists():
            for path in sorted(
                self.matches_dir.glob("*.json")
            ):
                if (
                    len(catalog)
                    >= len(target_puuids)
                ):
                    break

                try:
                    payload = json.loads(
                        path.read_text(
                            encoding="utf-8"
                        )
                    )
                except (
                    OSError,
                    ValueError,
                    TypeError,
                ):
                    continue

                participants = (
                    payload
                    .get("info", {})
                    .get("participants", [])
                )

                for participant in participants:
                    puuid = str(
                        participant.get(
                            "puuid",
                            "",
                        )
                    ).strip()

                    if (
                        not puuid
                        or puuid not in target_puuids
                        or puuid in catalog
                    ):
                        continue

                    game_name = str(
                        participant.get(
                            "riotIdGameName",
                            "",
                        )
                    ).strip()

                    tag_line = str(
                        participant.get(
                            "riotIdTagline",
                            "",
                        )
                    ).strip()

                    if not game_name:
                        continue

                    catalog[puuid] = {
                        "game_name": game_name,
                        "tag_line": tag_line,
                    }

        self.catalog_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.catalog_path.write_text(
            json.dumps(
                catalog,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return catalog

    def _build_players(
        self,
        rows: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        catalog = self._load_catalog()

        if not catalog:
            catalog = self.rebuild_player_catalog()

        players = []

        for row in rows:
            puuid = row["player"]
            identity = catalog.get(
                puuid,
                {},
            )

            game_name = identity.get(
                "game_name"
            )

            if not game_name:
                game_name = (
                    "Unknown "
                    + puuid[:8]
                )

            players.append(
                {
                    "puuid": puuid,
                    "game_name": game_name,
                    "tag_line": identity.get(
                        "tag_line",
                        "",
                    ),
                    "matches_played": int(
                        float(
                            row[
                                "matches_played"
                            ]
                        )
                    ),
                    "average_placement": float(
                        row[
                            "average_placement"
                        ]
                    ),
                    "top4_rate": float(
                        row["top4_rate"]
                    ),
                    "win_rate": float(
                        row["win_rate"]
                    ),
                    "average_level": float(
                        row["average_level"]
                    ),
                    "average_damage_to_players": float(
                        row[
                            "average_damage_to_players"
                        ]
                    ),
                }
            )

        return sorted(
            players,
            key=lambda item: (
                item["average_placement"],
                -item["top4_rate"],
            ),
        )

    def _aggregate_metrics(
        self,
        rows: list[dict[str, str]],
    ) -> dict[str, dict[str, float]]:
        output = {}

        for metric, config in self.METRICS.items():
            values = [
                float(row[metric])
                for row in rows
                if row.get(metric) not in {
                    None,
                    "",
                }
            ]

            if not values:
                continue

            ordered = sorted(values)

            output[metric] = {
                "label": config["label"],
                "mean": round(
                    mean(values),
                    2,
                ),
                "median": round(
                    median(values),
                    2,
                ),
                "minimum": round(
                    min(values),
                    2,
                ),
                "maximum": round(
                    max(values),
                    2,
                ),
                "q25": round(
                    self._percentile(
                        ordered,
                        0.25,
                    ),
                    2,
                ),
                "q75": round(
                    self._percentile(
                        ordered,
                        0.75,
                    ),
                    2,
                ),
            }

        return output

    def _load_rows(
        self,
    ) -> list[dict[str, str]]:
        if not self.metrics_path.exists():
            raise RuntimeError(
                "Dataset Challenger não encontrado: "
                f"{self.metrics_path}"
            )

        with self.metrics_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            rows = list(
                csv.DictReader(file)
            )

        if not rows:
            raise RuntimeError(
                "Dataset Challenger está vazio."
            )

        return rows

    def _load_catalog(
        self,
    ) -> dict[str, dict[str, Any]]:
        if not self.catalog_path.exists():
            return {}

        try:
            payload = json.loads(
                self.catalog_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            ValueError,
            TypeError,
        ):
            return {}

        return (
            payload
            if isinstance(payload, dict)
            else {}
        )

    @staticmethod
    def _performance_percentile(
        *,
        value: float,
        distribution: list[float],
        higher_is_better: bool,
    ) -> float:
        if not distribution:
            return 0.0

        if higher_is_better:
            count = sum(
                candidate <= value
                for candidate in distribution
            )
        else:
            count = sum(
                candidate >= value
                for candidate in distribution
            )

        return (
            count
            / len(distribution)
            * 100.0
        )

    @staticmethod
    def _assessment(
        percentile: float,
    ) -> str:
        if percentile >= 90:
            return "Elite Challenger level"
        if percentile >= 75:
            return "Above Challenger median"
        if percentile >= 55:
            return "Near upper Challenger range"
        if percentile >= 40:
            return "Near Challenger median"
        if percentile >= 20:
            return "Below Challenger median"
        return "Large gap to Challenger reference"

    @staticmethod
    def _overall_classification(
        percentile: float,
    ) -> str:
        if percentile >= 85:
            return "Challenger-like"
        if percentile >= 65:
            return "Very competitive"
        if percentile >= 45:
            return "Competitive"
        if percentile >= 25:
            return "Developing"
        return "Large benchmark gap"

    @staticmethod
    def _percentile(
        ordered: list[float],
        fraction: float,
    ) -> float:
        if len(ordered) == 1:
            return ordered[0]

        position = (
            fraction
            * (len(ordered) - 1)
        )
        lower = int(position)
        upper = min(
            lower + 1,
            len(ordered) - 1,
        )
        weight = position - lower

        return (
            ordered[lower]
            + (
                ordered[upper]
                - ordered[lower]
            )
            * weight
        )
