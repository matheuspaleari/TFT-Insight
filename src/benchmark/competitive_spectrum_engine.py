"""
Competitive Spectrum Engine V1.

Responsabilidade:
- posicionar o elo atual dentro do grupo competitivo;
- calcular percentil empírico contra o catálogo real;
- classificar a posição em Entrada / Consolidação / Avançado / Transição;
- resumir o perfil comparativo já produzido pelo Performance Engine.

Proteções:
- não estima chance de subir;
- não declara "pronto para subir";
- não transforma X/Y métricas em requisito de promoção;
- não cria pesos universais a partir das correlações exploratórias.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.performance_engine.models import Performance

from .competitive_spectrum_diagnostic import (
    rank_sort_key,
    spectrum_band,
    theoretical_position,
)
from .player_catalog import BenchmarkPlayerCatalogRepository


@dataclass(slots=True, frozen=True)
class SpectrumMetricProfile:
    metric: str
    score: float
    player_value: float
    benchmark_value: float
    classification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "score": self.score,
            "player_value": self.player_value,
            "benchmark_value": self.benchmark_value,
            "classification": self.classification,
        }


@dataclass(slots=True, frozen=True)
class CompetitiveSpectrumResult:
    available: bool
    benchmark_id: str
    group_label: str
    current_rank: str
    spectrum_position: float | None = None
    spectrum_percentile: float | None = None
    spectrum_band: str | None = None
    spectrum_band_id: str | None = None
    population_size: int = 0
    strengths: tuple[str, ...] = field(default_factory=tuple)
    neutral_areas: tuple[str, ...] = field(default_factory=tuple)
    attention_areas: tuple[str, ...] = field(default_factory=tuple)
    performance_profile: tuple[SpectrumMetricProfile, ...] = field(
        default_factory=tuple
    )
    limitation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "benchmark_id": self.benchmark_id,
            "group_label": self.group_label,
            "current_rank": self.current_rank,
            "spectrum_position": self.spectrum_position,
            "spectrum_percentile": self.spectrum_percentile,
            "spectrum_band": self.spectrum_band,
            "spectrum_band_id": self.spectrum_band_id,
            "population_size": self.population_size,
            "strengths": list(self.strengths),
            "neutral_areas": list(self.neutral_areas),
            "attention_areas": list(self.attention_areas),
            "performance_profile": [
                item.to_dict()
                for item in self.performance_profile
            ],
            "limitation": self.limitation,
        }


class CompetitiveSpectrumEngine:
    """
    Produz contexto competitivo descritivo usando catálogo real + Performance.
    """

    STRONG_SCORE = 60.0
    ATTENTION_SCORE = 40.0

    def __init__(
        self,
        *,
        benchmark_directory: str | Path = "data/benchmark",
    ) -> None:
        self.repository = BenchmarkPlayerCatalogRepository(
            directory=benchmark_directory
        )

    def analyze(
        self,
        *,
        benchmark_id: str,
        group_label: str,
        tier: str | None,
        division: str | None,
        league_points: int | None,
        current_rank: str,
        performance: Performance | None = None,
    ) -> CompetitiveSpectrumResult:
        benchmark_id = benchmark_id.strip().lower()

        if not tier:
            return self._unavailable(
                benchmark_id=benchmark_id,
                group_label=group_label,
                current_rank=current_rank,
                limitation=(
                    "Jogador sem elo RANKED_TFT; posição competitiva "
                    "não pode ser calculada."
                ),
                performance=performance,
            )

        tier = tier.strip().upper()
        division = (division or "").strip().upper()
        lp = int(league_points or 0)

        catalog = self.repository.load(benchmark_id)

        if not catalog:
            return self._unavailable(
                benchmark_id=benchmark_id,
                group_label=group_label,
                current_rank=current_rank,
                limitation=(
                    "Catálogo individual do grupo competitivo não está disponível."
                ),
                performance=performance,
            )

        position = theoretical_position(
            benchmark_id=benchmark_id,
            tier=tier,
            division=division,
            league_points=lp,
        )

        if position is None:
            return self._unavailable(
                benchmark_id=benchmark_id,
                group_label=group_label,
                current_rank=current_rank,
                limitation=(
                    "O elo atual está fora do espectro configurado "
                    "para este benchmark."
                ),
                performance=performance,
            )

        player_key = rank_sort_key(
            tier=tier,
            division=division,
            league_points=lp,
        )

        catalog_keys = sorted(
            rank_sort_key(
                tier=item.current_tier,
                division=item.current_division,
                league_points=item.current_league_points,
            )
            for item in catalog
        )

        below = sum(
            1
            for item in catalog_keys
            if item < player_key
        )
        equal = sum(
            1
            for item in catalog_keys
            if item == player_key
        )

        percentile = (
            (below + 0.5 * equal)
            / len(catalog_keys)
        )
        percentile = max(0.0, min(1.0, percentile))

        band_id, band_label = spectrum_band(percentile)

        profile = self._performance_profile(performance)

        strengths = tuple(
            item.metric
            for item in profile
            if item.classification == "STRENGTH"
        )
        neutral = tuple(
            item.metric
            for item in profile
            if item.classification == "NEUTRAL"
        )
        attention = tuple(
            item.metric
            for item in profile
            if item.classification == "ATTENTION"
        )

        return CompetitiveSpectrumResult(
            available=True,
            benchmark_id=benchmark_id,
            group_label=group_label,
            current_rank=current_rank,
            spectrum_position=round(position, 4),
            spectrum_percentile=round(percentile, 4),
            spectrum_band=band_label,
            spectrum_band_id=band_id,
            population_size=len(catalog),
            strengths=strengths,
            neutral_areas=neutral,
            attention_areas=attention,
            performance_profile=profile,
        )

    def _unavailable(
        self,
        *,
        benchmark_id: str,
        group_label: str,
        current_rank: str,
        limitation: str,
        performance: Performance | None,
    ) -> CompetitiveSpectrumResult:
        profile = self._performance_profile(performance)

        return CompetitiveSpectrumResult(
            available=False,
            benchmark_id=benchmark_id,
            group_label=group_label,
            current_rank=current_rank,
            performance_profile=profile,
            strengths=tuple(
                item.metric
                for item in profile
                if item.classification == "STRENGTH"
            ),
            neutral_areas=tuple(
                item.metric
                for item in profile
                if item.classification == "NEUTRAL"
            ),
            attention_areas=tuple(
                item.metric
                for item in profile
                if item.classification == "ATTENTION"
            ),
            limitation=limitation,
        )

    def _performance_profile(
        self,
        performance: Performance | None,
    ) -> tuple[SpectrumMetricProfile, ...]:
        if performance is None:
            return ()

        result = []

        for evaluation in performance.evaluations:
            score = float(evaluation.score)

            if score >= self.STRONG_SCORE:
                classification = "STRENGTH"
            elif score < self.ATTENTION_SCORE:
                classification = "ATTENTION"
            else:
                classification = "NEUTRAL"

            result.append(
                SpectrumMetricProfile(
                    metric=evaluation.metric.value,
                    score=round(score, 2),
                    player_value=round(
                        float(evaluation.player_value),
                        4,
                    ),
                    benchmark_value=round(
                        float(evaluation.benchmark_metric.mean),
                        4,
                    ),
                    classification=classification,
                )
            )

        return tuple(result)
