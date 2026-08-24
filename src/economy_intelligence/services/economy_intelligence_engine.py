from __future__ import annotations

from statistics import mean, median

from src.decision_engine.models import EconomyReport
from src.performance_engine.models import Match

from src.economy_intelligence.models.economy_intelligence import (
    EconomyFinalStateDistribution,
    EconomyIntelligenceReport,
    EconomyPlacementComparison,
    EconomyRecentTrend,
    LatestEconomySnapshot,
)


class EconomyIntelligenceEngine:
    """
    Enriquece o EconomyHistoryAnalyzer existente.

    O módulo descreve estados finais e padrões históricos.
    Ele NÃO reconstrói:
    - timing de compra de XP;
    - timing de roll;
    - estabilização;
    - intenção de guardar/gastar ouro.
    """

    MIN_GROUP_SAMPLE = 3
    TREND_BLOCK_SIZE = 10

    @classmethod
    def build(
        cls,
        *,
        matches: list[Match],
        base_report: EconomyReport,
    ) -> EconomyIntelligenceReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        levels = [match.level for match in matches]
        gold = [match.gold_left for match in matches]

        return EconomyIntelligenceReport(
            matches_analyzed=len(matches),
            score=base_report.score,
            label=base_report.label,
            average_level=base_report.average_level,
            median_level=round(median(levels), 2),
            average_gold_left=base_report.average_gold_left,
            median_gold_left=round(median(gold), 2),
            average_last_round=base_report.average_last_round,
            level_8_rate=base_report.level_8_rate,
            level_9_rate=base_report.level_9_rate,
            low_level_late_rate=base_report.low_level_late_rate,
            distribution=cls._distribution(matches),
            placement_comparison=cls._placement_comparison(matches),
            recent_trend=cls._recent_trend(matches),
            latest=LatestEconomySnapshot(
                match_id=matches[0].match_id,
                placement=matches[0].placement,
                level=matches[0].level,
                gold_left=matches[0].gold_left,
                last_round=matches[0].last_round,
            ),
            limitations=(
                "Ouro restante é um estado final; não mostra quando nem por que o ouro foi gasto ou guardado.",
                "Nível final não informa o timing de compra de experiência.",
                "A Riot API não registra cada roll, compra, venda ou decisão de estabilização.",
                "Associações entre nível final e colocação não provam que subir de nível causou o resultado.",
                "O sistema não afirma que terminar com muito ou pouco ouro foi correto ou incorreto isoladamente.",
            ),
        )

    @staticmethod
    def _distribution(
        matches: list[Match],
    ) -> EconomyFinalStateDistribution:
        return EconomyFinalStateDistribution(
            gold_0_to_5=sum(match.gold_left <= 5 for match in matches),
            gold_6_to_19=sum(6 <= match.gold_left <= 19 for match in matches),
            gold_20_plus=sum(match.gold_left >= 20 for match in matches),
            level_7_or_lower=sum(match.level <= 7 for match in matches),
            level_8=sum(match.level == 8 for match in matches),
            level_9_plus=sum(match.level >= 9 for match in matches),
        )

    @classmethod
    def _placement_comparison(
        cls,
        matches: list[Match],
    ) -> EconomyPlacementComparison:
        level_9 = [
            match.placement
            for match in matches
            if match.level >= 9
        ]
        below = [
            match.placement
            for match in matches
            if match.level < 9
        ]

        level_9_avg = (
            round(mean(level_9), 2)
            if level_9
            else None
        )
        below_avg = (
            round(mean(below), 2)
            if below
            else None
        )

        delta = (
            round(level_9_avg - below_avg, 2)
            if level_9_avg is not None
            and below_avg is not None
            else None
        )

        return EconomyPlacementComparison(
            level_9_plus_matches=len(level_9),
            below_level_9_matches=len(below),
            level_9_plus_average_placement=level_9_avg,
            below_level_9_average_placement=below_avg,
            placement_delta=delta,
            eligible_for_comparison=(
                len(level_9) >= cls.MIN_GROUP_SAMPLE
                and len(below) >= cls.MIN_GROUP_SAMPLE
            ),
        )

    @classmethod
    def _recent_trend(
        cls,
        matches: list[Match],
    ) -> EconomyRecentTrend:
        block = min(
            cls.TREND_BLOCK_SIZE,
            len(matches) // 2,
        )

        if block < 3:
            return EconomyRecentTrend(
                recent_matches=0,
                previous_matches=0,
                recent_average_level=None,
                previous_average_level=None,
                level_delta=None,
                recent_average_gold_left=None,
                previous_average_gold_left=None,
                gold_delta=None,
                recent_average_placement=None,
                previous_average_placement=None,
                placement_delta=None,
                signal="HISTORICO_INSUFICIENTE",
            )

        recent = matches[:block]
        previous = matches[block:block * 2]

        recent_level = round(
            mean(match.level for match in recent),
            2,
        )
        previous_level = round(
            mean(match.level for match in previous),
            2,
        )
        recent_gold = round(
            mean(match.gold_left for match in recent),
            2,
        )
        previous_gold = round(
            mean(match.gold_left for match in previous),
            2,
        )
        recent_placement = round(
            mean(match.placement for match in recent),
            2,
        )
        previous_placement = round(
            mean(match.placement for match in previous),
            2,
        )

        level_delta = round(
            recent_level - previous_level,
            2,
        )
        gold_delta = round(
            recent_gold - previous_gold,
            2,
        )
        placement_delta = round(
            recent_placement - previous_placement,
            2,
        )

        # Sinal descritivo da progressão final, não de "qualidade da economia".
        if level_delta >= 0.35:
            signal = "NIVEL_FINAL_MAIS_ALTO"
        elif level_delta <= -0.35:
            signal = "NIVEL_FINAL_MAIS_BAIXO"
        else:
            signal = "NIVEL_FINAL_ESTAVEL"

        return EconomyRecentTrend(
            recent_matches=len(recent),
            previous_matches=len(previous),
            recent_average_level=recent_level,
            previous_average_level=previous_level,
            level_delta=level_delta,
            recent_average_gold_left=recent_gold,
            previous_average_gold_left=previous_gold,
            gold_delta=gold_delta,
            recent_average_placement=recent_placement,
            previous_average_placement=previous_placement,
            placement_delta=placement_delta,
            signal=signal,
        )
