"""
Diagnóstico exploratório do espectro competitivo dos benchmarks.

Esta versão NÃO altera benchmark, Coach, Skill, Learning Priority ou UI.
Ela apenas lê *_player_catalog.json e mede:

- distribuição real de elo/divisão/LP;
- posição teórica e posição empírica no grupo;
- faixas do espectro;
- médias das métricas por faixa;
- correlação de Spearman entre posição competitiva e métricas.

A correlação é descritiva. Ela NÃO cria pesos de Coach automaticamente.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


TIER_ORDER = {
    "IRON": 0,
    "BRONZE": 1,
    "SILVER": 2,
    "GOLD": 3,
    "PLATINUM": 4,
    "EMERALD": 5,
    "DIAMOND": 6,
    "MASTER": 7,
    "GRANDMASTER": 8,
    "CHALLENGER": 9,
}

DIVISION_ORDER = {
    "IV": 0,
    "III": 1,
    "II": 2,
    "I": 3,
}

BENCHMARK_SPECTRA = {
    "novice": (
        ("IRON", ("IV", "III", "II", "I")),
        ("BRONZE", ("IV", "III", "II", "I")),
        ("SILVER", ("IV", "III", "II", "I")),
    ),
    "intermediate": (
        ("GOLD", ("IV", "III", "II", "I")),
        ("PLATINUM", ("IV", "III", "II", "I")),
    ),
    "advanced": (
        ("EMERALD", ("IV", "III", "II", "I")),
        ("DIAMOND", ("IV", "III", "II", "I")),
    ),
    "expert": (
        ("MASTER", ()),
    ),
    "elite": (
        ("GRANDMASTER", ()),
        ("CHALLENGER", ()),
    ),
}

SPECTRUM_BANDS = (
    (0.00, 0.25, "ENTRY", "Entrada"),
    (0.25, 0.50, "CONSOLIDATION", "Consolidação"),
    (0.50, 0.75, "ADVANCED", "Avançado"),
    (0.75, 1.01, "TRANSITION", "Transição"),
)

METRICS = {
    "average_placement": ("general", "average_placement"),
    "top4_rate": ("general", "top4_rate"),
    "win_rate": ("general", "win_rate"),
    "average_level": ("general", "average_level"),
    "placement_standard_deviation": (
        "consistency",
        "placement_standard_deviation",
    ),
    "bottom4_rate": ("consistency", "bottom4_rate"),
    "average_damage_to_players": (
        "combat",
        "average_damage_to_players",
    ),
    "average_players_eliminated": (
        "combat",
        "average_players_eliminated",
    ),
    "average_gold_left": ("economy", "average_gold_left"),
}

LOWER_IS_BETTER = {
    "average_placement",
    "placement_standard_deviation",
    "bottom4_rate",
}


@dataclass(slots=True)
class SpectrumPlayer:
    benchmark_id: str
    game_name: str
    tag_line: str
    tier: str
    division: str
    league_points: int
    theoretical_position: float
    empirical_percentile: float
    band_id: str
    band_label: str
    metrics: dict[str, float | None]

    @property
    def riot_id(self) -> str:
        if self.game_name and self.tag_line:
            return f"{self.game_name}#{self.tag_line}"
        return "-"


class CompetitiveSpectrumDiagnostic:
    def __init__(
        self,
        *,
        benchmark_directory: str | Path = "data/benchmark",
        output_directory: str | Path = "data/benchmark/spectrum_diagnostic",
    ) -> None:
        self.benchmark_directory = Path(benchmark_directory)
        self.output_directory = Path(output_directory)

    def available_catalogs(self) -> list[str]:
        result = []
        for benchmark_id in BENCHMARK_SPECTRA:
            path = self._catalog_path(benchmark_id)
            if path.exists():
                result.append(benchmark_id)
        return result

    def analyze(
        self,
        benchmark_id: str,
    ) -> dict[str, Any]:
        benchmark_id = benchmark_id.strip().lower()

        if benchmark_id not in BENCHMARK_SPECTRA:
            raise ValueError(
                f"Benchmark não suportado: {benchmark_id}"
            )

        catalog = self._load_catalog(benchmark_id)
        raw_players = catalog.get("players", [])

        if not isinstance(raw_players, list) or not raw_players:
            raise RuntimeError(
                f"Catálogo sem jogadores: {benchmark_id}"
            )

        prepared = [
            self._prepare_base_player(
                benchmark_id=benchmark_id,
                payload=item,
            )
            for item in raw_players
            if isinstance(item, dict)
        ]

        prepared = [
            item
            for item in prepared
            if item is not None
        ]

        if not prepared:
            raise RuntimeError(
                f"Nenhum jogador válido no catálogo {benchmark_id}."
            )

        # Percentil empírico usa a ordem competitiva real da própria amostra.
        ordered = sorted(
            prepared,
            key=lambda item: item["rank_sort_key"],
        )

        empirical_by_identity: dict[str, float] = {}

        if len(ordered) == 1:
            empirical_by_identity[
                ordered[0]["identity_key"]
            ] = 0.5
        else:
            for index, item in enumerate(ordered):
                empirical_by_identity[
                    item["identity_key"]
                ] = index / (len(ordered) - 1)

        players: list[SpectrumPlayer] = []

        for item in prepared:
            empirical = empirical_by_identity[
                item["identity_key"]
            ]
            band_id, band_label = spectrum_band(
                empirical
            )

            players.append(
                SpectrumPlayer(
                    benchmark_id=benchmark_id,
                    game_name=item["game_name"],
                    tag_line=item["tag_line"],
                    tier=item["tier"],
                    division=item["division"],
                    league_points=item["league_points"],
                    theoretical_position=item["theoretical_position"],
                    empirical_percentile=empirical,
                    band_id=band_id,
                    band_label=band_label,
                    metrics=item["metrics"],
                )
            )

        report = {
            "benchmark_id": benchmark_id,
            "players_count": len(players),
            "rank_distribution": self._rank_distribution(
                players
            ),
            "band_distribution": self._band_distribution(
                players
            ),
            "metric_correlations": self._metric_correlations(
                players
            ),
            "band_metric_summary": self._band_metric_summary(
                players
            ),
            "players": [
                self._player_to_dict(player)
                for player in sorted(
                    players,
                    key=lambda item: item.empirical_percentile,
                )
            ],
            "methodology": {
                "theoretical_position": (
                    "Posição contínua calculada a partir de tier, divisão e LP "
                    "dentro do espectro configurado do benchmark."
                ),
                "empirical_percentile": (
                    "Posição relativa do jogador dentro dos jogadores realmente "
                    "presentes no catálogo, ordenados por elo/divisão/LP."
                ),
                "correlation": (
                    "Spearman entre percentil empírico e métrica individual. "
                    "Correlação não implica causalidade e não cria pesos automaticamente."
                ),
            },
        }

        return report

    def save_report(
        self,
        report: dict[str, Any],
    ) -> tuple[Path, Path]:
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        benchmark_id = report["benchmark_id"]

        json_path = (
            self.output_directory
            / f"{benchmark_id}_competitive_spectrum.json"
        )

        csv_path = (
            self.output_directory
            / f"{benchmark_id}_competitive_spectrum_players.csv"
        )

        json_path.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        players = report["players"]

        fieldnames = [
            "riot_id",
            "tier",
            "division",
            "league_points",
            "theoretical_position",
            "empirical_percentile",
            "band",
            *METRICS.keys(),
        ]

        with csv_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
            )
            writer.writeheader()

            for player in players:
                row = {
                    "riot_id": player["riot_id"],
                    "tier": player["tier"],
                    "division": player["division"],
                    "league_points": player["league_points"],
                    "theoretical_position": round(
                        player["theoretical_position"] * 100,
                        2,
                    ),
                    "empirical_percentile": round(
                        player["empirical_percentile"] * 100,
                        2,
                    ),
                    "band": player["band_label"],
                }
                row.update(player["metrics"])
                writer.writerow(row)

        return json_path, csv_path

    def _load_catalog(
        self,
        benchmark_id: str,
    ) -> dict[str, Any]:
        path = self._catalog_path(
            benchmark_id
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Catálogo não encontrado: {path}"
            )

        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                f"Formato inválido: {path}"
            )

        return data

    def _catalog_path(
        self,
        benchmark_id: str,
    ) -> Path:
        return (
            self.benchmark_directory
            / f"{benchmark_id}_player_catalog.json"
        )

    def _prepare_base_player(
        self,
        *,
        benchmark_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        tier = str(
            payload.get(
                "current_tier",
                payload.get("tier_at_collection", ""),
            )
        ).strip().upper()

        division = str(
            payload.get(
                "current_division",
                payload.get(
                    "division_at_collection",
                    "",
                ),
            )
            or ""
        ).strip().upper()

        league_points = int(
            payload.get(
                "current_league_points",
                payload.get(
                    "league_points_at_collection",
                    0,
                ),
            )
            or 0
        )

        if tier not in TIER_ORDER:
            return None

        theoretical = theoretical_position(
            benchmark_id=benchmark_id,
            tier=tier,
            division=division,
            league_points=league_points,
        )

        if theoretical is None:
            return None

        puuid = str(
            payload.get("puuid", "")
        )

        game_name = str(
            payload.get("game_name") or ""
        )
        tag_line = str(
            payload.get("tag_line") or ""
        )

        identity_key = (
            puuid
            or f"{game_name.lower()}#{tag_line.lower()}"
        )

        metrics_payload = payload.get(
            "metrics",
            {},
        )

        metrics: dict[str, float | None] = {}

        for metric_id, path in METRICS.items():
            value = nested_number(
                metrics_payload,
                path,
            )
            metrics[metric_id] = value

        return {
            "identity_key": identity_key,
            "game_name": game_name,
            "tag_line": tag_line,
            "tier": tier,
            "division": division,
            "league_points": league_points,
            "theoretical_position": theoretical,
            "rank_sort_key": rank_sort_key(
                tier=tier,
                division=division,
                league_points=league_points,
            ),
            "metrics": metrics,
        }

    @staticmethod
    def _rank_distribution(
        players: list[SpectrumPlayer],
    ) -> dict[str, int]:
        counts = Counter(
            rank_label(
                player.tier,
                player.division,
            )
            for player in players
        )

        return dict(
            sorted(
                counts.items(),
                key=lambda item: rank_label_sort_key(
                    item[0]
                ),
            )
        )

    @staticmethod
    def _band_distribution(
        players: list[SpectrumPlayer],
    ) -> dict[str, int]:
        counts = Counter(
            player.band_label
            for player in players
        )
        return {
            band_label: counts.get(
                band_label,
                0,
            )
            for _, _, _, band_label in SPECTRUM_BANDS
        }

    @staticmethod
    def _metric_correlations(
        players: list[SpectrumPlayer],
    ) -> list[dict[str, Any]]:
        result = []

        positions = [
            player.empirical_percentile
            for player in players
        ]

        for metric_id in METRICS:
            paired = [
                (
                    positions[index],
                    player.metrics.get(metric_id),
                )
                for index, player in enumerate(players)
                if player.metrics.get(metric_id) is not None
            ]

            if len(paired) < 5:
                correlation = None
            else:
                correlation = spearman(
                    [item[0] for item in paired],
                    [float(item[1]) for item in paired],
                )

            adjusted = correlation

            if (
                adjusted is not None
                and metric_id in LOWER_IS_BETTER
            ):
                adjusted *= -1

            result.append(
                {
                    "metric": metric_id,
                    "players": len(paired),
                    "raw_spearman": (
                        round(correlation, 4)
                        if correlation is not None
                        else None
                    ),
                    "progression_signal": (
                        round(adjusted, 4)
                        if adjusted is not None
                        else None
                    ),
                    "interpretation": correlation_label(
                        adjusted
                    ),
                    "lower_is_better": (
                        metric_id in LOWER_IS_BETTER
                    ),
                }
            )

        return sorted(
            result,
            key=lambda item: (
                abs(
                    item["progression_signal"]
                    if item["progression_signal"] is not None
                    else -999
                )
            ),
            reverse=True,
        )

    @staticmethod
    def _band_metric_summary(
        players: list[SpectrumPlayer],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for _, _, band_id, band_label in SPECTRUM_BANDS:
            band_players = [
                player
                for player in players
                if player.band_id == band_id
            ]

            metrics_summary = {}

            for metric_id in METRICS:
                values = [
                    float(player.metrics[metric_id])
                    for player in band_players
                    if player.metrics.get(metric_id) is not None
                ]

                metrics_summary[metric_id] = (
                    round(mean(values), 4)
                    if values
                    else None
                )

            result[band_label] = {
                "players": len(band_players),
                "metrics": metrics_summary,
            }

        return result

    @staticmethod
    def _player_to_dict(
        player: SpectrumPlayer,
    ) -> dict[str, Any]:
        return {
            "riot_id": player.riot_id,
            "tier": player.tier,
            "division": player.division,
            "league_points": player.league_points,
            "theoretical_position": round(
                player.theoretical_position,
                6,
            ),
            "empirical_percentile": round(
                player.empirical_percentile,
                6,
            ),
            "band_id": player.band_id,
            "band_label": player.band_label,
            "metrics": player.metrics,
        }


def theoretical_position(
    *,
    benchmark_id: str,
    tier: str,
    division: str,
    league_points: int,
) -> float | None:
    spectrum = BENCHMARK_SPECTRA.get(
        benchmark_id
    )

    if not spectrum:
        return None

    # Grupos com divisões: cada divisão ocupa 100 LP.
    has_divisions = any(
        bool(divisions)
        for _, divisions in spectrum
    )

    if has_divisions:
        slots = []

        for slot_tier, divisions in spectrum:
            for slot_division in divisions:
                slots.append(
                    (
                        slot_tier,
                        slot_division,
                    )
                )

        try:
            slot_index = slots.index(
                (tier, division)
            )
        except ValueError:
            return None

        total_units = len(slots) * 100
        current_units = (
            slot_index * 100
            + clamp_lp(league_points)
        )

        return min(
            max(
                current_units / total_units,
                0.0,
            ),
            1.0,
        )

    # Apex: tier define o bloco e LP posiciona dentro dele.
    # Como LP não possui teto rígido, o percentil empírico será o sinal principal.
    tier_slots = [
        item[0]
        for item in spectrum
    ]

    try:
        tier_index = tier_slots.index(tier)
    except ValueError:
        return None

    if len(tier_slots) == 1:
        # Para Master puro, posição teórica absoluta por LP não é confiável.
        # Normalização suave apenas para visualização; ranking real usa percentil.
        return min(
            max(league_points / 1000.0, 0.0),
            1.0,
        )

    # Elite: GM ocupa metade inferior, Challenger metade superior.
    base = tier_index / len(tier_slots)
    width = 1.0 / len(tier_slots)
    lp_component = min(
        max(league_points / 2000.0, 0.0),
        1.0,
    )

    return min(
        base + width * lp_component,
        1.0,
    )


def rank_sort_key(
    *,
    tier: str,
    division: str,
    league_points: int,
) -> tuple[int, int, int]:
    return (
        TIER_ORDER.get(tier, -1),
        DIVISION_ORDER.get(division, 0),
        league_points,
    )


def rank_label(
    tier: str,
    division: str,
) -> str:
    return (
        f"{tier} {division}".strip()
    )


def rank_label_sort_key(
    label: str,
) -> tuple[int, int]:
    parts = label.split()
    tier = parts[0] if parts else ""
    division = (
        parts[1]
        if len(parts) > 1
        else ""
    )
    return (
        TIER_ORDER.get(tier, -1),
        DIVISION_ORDER.get(division, 0),
    )


def spectrum_band(
    percentile: float,
) -> tuple[str, str]:
    for minimum, maximum, band_id, band_label in SPECTRUM_BANDS:
        if minimum <= percentile < maximum:
            return band_id, band_label

    return "TRANSITION", "Transição"


def nested_number(
    payload: Any,
    path: tuple[str, ...],
) -> float | None:
    node = payload

    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)

    if isinstance(node, bool):
        return None

    if isinstance(node, (int, float)):
        value = float(node)
        if math.isfinite(value):
            return value

    return None


def clamp_lp(value: int) -> int:
    return max(
        0,
        min(int(value), 99),
    )


def correlation_label(
    value: float | None,
) -> str:
    if value is None:
        return "INSUFFICIENT_DATA"

    magnitude = abs(value)

    if magnitude < 0.10:
        return "VERY_WEAK"

    if magnitude < 0.25:
        return "WEAK"

    if magnitude < 0.45:
        return "MODERATE"

    if magnitude < 0.65:
        return "STRONG"

    return "VERY_STRONG"


def spearman(
    x: list[float],
    y: list[float],
) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None

    rank_x = average_ranks(x)
    rank_y = average_ranks(y)

    return pearson(
        rank_x,
        rank_y,
    )


def average_ranks(
    values: list[float],
) -> list[float]:
    indexed = sorted(
        enumerate(values),
        key=lambda item: item[1],
    )

    ranks = [0.0] * len(values)
    position = 0

    while position < len(indexed):
        end = position

        while (
            end + 1 < len(indexed)
            and indexed[end + 1][1]
            == indexed[position][1]
        ):
            end += 1

        average_rank = (
            (position + 1)
            + (end + 1)
        ) / 2.0

        for cursor in range(
            position,
            end + 1,
        ):
            original_index = indexed[cursor][0]
            ranks[original_index] = average_rank

        position = end + 1

    return ranks


def pearson(
    x: list[float],
    y: list[float],
) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None

    mean_x = mean(x)
    mean_y = mean(y)

    numerator = sum(
        (a - mean_x) * (b - mean_y)
        for a, b in zip(x, y)
    )

    denominator_x = math.sqrt(
        sum(
            (a - mean_x) ** 2
            for a in x
        )
    )

    denominator_y = math.sqrt(
        sum(
            (b - mean_y) ** 2
            for b in y
        )
    )

    denominator = (
        denominator_x
        * denominator_y
    )

    if denominator == 0:
        return None

    return numerator / denominator
