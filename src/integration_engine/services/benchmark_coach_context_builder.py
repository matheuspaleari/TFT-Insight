from __future__ import annotations

from pathlib import Path

from src.decision_engine import (
    CompositionHistoryAnalyzer,
    ContestHistoryAnalyzer,
)
from src.decision_engine.analyzers.strategic_decision_engine import (
    StrategicDecisionEngine,
)
from src.integration_engine.services.item_classification_provider import (
    ItemClassificationProvider,
)
from src.performance_engine.models import Match
from src.recommendation_engine.services.composition_recommendation_engine import (
    CompositionRecommendationEngine,
)
from src.recommendation_engine.services.contest_recommendation_engine import (
    ContestRecommendationEngine,
)
from src.recommendation_engine.services.economy_recommendation_engine import (
    EconomyRecommendationEngine,
)


def _contest_impact_semantics(
    placement_impact: float | None,
) -> tuple[str, str]:
    if placement_impact is None:
        return (
            "indeterminado",
            "A amostra não permite medir o impacto da contestação na colocação.",
        )

    impact = float(placement_impact)

    if impact >= 1.0:
        return (
            "alto",
            (
                "As partidas contestadas apresentam piora média de pelo menos "
                f"1 posição ({impact:+.2f}) e esse efeito deve ser tratado "
                "como prioridade."
            ),
        )

    if impact >= 0.5:
        return (
            "relevante",
            (
                "As partidas contestadas apresentam piora média perceptível "
                f"na colocação ({impact:+.2f} posições), suficiente para "
                "merecer atenção no processo de decisão."
            ),
        )

    if impact > 0.0:
        return (
            "leve",
            (
                "Há uma piora média pequena nas partidas contestadas "
                f"({impact:+.2f} posições). O sinal existe, mas não deve "
                "ser tratado isoladamente como causa dos resultados."
            ),
        )

    if impact <= -0.5:
        return (
            "sem_piora_observada",
            (
                "A amostra não mostra piora de colocação associada à "
                f"contestação ({impact:+.2f} posições)."
            ),
        )

    return (
        "neutro",
        (
            "A diferença de colocação entre partidas contestadas e não "
            f"contestadas é pequena ({impact:+.2f} posições), portanto "
            "o histórico não sustenta impacto relevante."
        ),
    )


def _composition_semantics(
    *,
    diversity_rate: float,
    repetition_rate: float,
    forces_composition: bool,
) -> tuple[str, str]:
    if forces_composition:
        return (
            "concentrada",
            (
                "O histórico mostra concentração elevada em uma mesma linha "
                "de composição. Isso indica rigidez de padrão, mas não prova "
                "sozinho intenção de forçar composição em toda partida."
            ),
        )

    if repetition_rate >= 35.0:
        return (
            "preferência_clara",
            (
                "Existe preferência recorrente por algumas linhas, sem "
                "evidência suficiente de concentração extrema."
            ),
        )

    if diversity_rate >= 70.0:
        return (
            "muito_flexível",
            (
                "O histórico mostra alta variedade entre composições e não "
                "indica concentração excessiva em uma única linha."
            ),
        )

    if diversity_rate >= 50.0:
        return (
            "flexível",
            (
                "O histórico mostra variedade razoável de composições, com "
                "algum espaço para ampliar a flexibilidade."
            ),
        )

    return (
        "pouco_flexível",
        (
            "A variedade de composições é baixa na amostra e merece atenção "
            "como possível sinal de rigidez entre partidas."
        ),
    )


def _economy_semantics(
    *,
    label: str,
    average_gold_left: float,
    level_8_rate: float,
    level_9_rate: float,
    low_level_late_rate: float,
) -> str:
    normalized = label.strip().lower()

    if normalized in {"muito forte", "forte"}:
        return (
            f"A progressão econômica é uma força do histórico: nível 8 em "
            f"{level_8_rate:.1f}% das partidas, nível 9 em "
            f"{level_9_rate:.1f}% e apenas {low_level_late_rate:.1f}% de "
            "partidas longas terminando em nível baixo."
        )

    if average_gold_left >= 25.0 and level_9_rate < 30.0:
        return (
            "O histórico mostra recursos finais disponíveis com baixa "
            "frequência de nível 9, indicando espaço para converter melhor "
            "ouro em força antes da eliminação."
        )

    if low_level_late_rate >= 25.0:
        return (
            "Partidas longas terminam em nível baixo com frequência relevante, "
            "indicando que a progressão final merece atenção."
        )

    return (
        "A economia apresenta um padrão intermediário na amostra e deve ser "
        "interpretada junto dos demais sinais estratégicos."
    )


class BenchmarkCoachContextBuilder:
    """
    Reaproveita os analyzers/recommendation engines já existentes para
    enriquecer o Benchmark Intelligence.

    Nenhuma conclusão é produzida por IA nesta camada.
    O contexto representa fatos e recomendações determinísticas calculadas
    a partir do histórico oficial disponível.
    """

    @classmethod
    def build(
        cls,
        *,
        project_root: Path,
        matches: list[Match],
    ) -> dict:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        classifications = ItemClassificationProvider(
            project_root=project_root
        ).get()

        contest_history = ContestHistoryAnalyzer.analyze(
            matches
        )

        composition_history = CompositionHistoryAnalyzer.analyze(
            matches,
            contest_history=contest_history,
            item_classifications=classifications,
        )

        strategic_report = StrategicDecisionEngine.analyze(
            matches,
            item_classifications=classifications,
        )

        contest_recommendation = (
            ContestRecommendationEngine.recommend(
                contest_history=contest_history,
            )
        )

        economy_recommendation = (
            EconomyRecommendationEngine.recommend(
                strategic_report=strategic_report,
            )
        )

        composition_recommendations = (
            CompositionRecommendationEngine.recommend(
                composition_history=composition_history,
                limit=5,
            )
        )

        most_used = composition_history.most_used_composition
        best = composition_history.best_composition
        latest_contest = contest_history.latest_report
        economy = strategic_report.economy

        (
            contest_impact_label,
            contest_impact_interpretation,
        ) = _contest_impact_semantics(
            contest_history.placement_impact
        )

        (
            flexibility_label,
            flexibility_interpretation,
        ) = _composition_semantics(
            diversity_rate=composition_history.diversity_rate,
            repetition_rate=composition_history.repetition_rate,
            forces_composition=composition_history.forces_composition,
        )

        economy_interpretation = _economy_semantics(
            label=economy.label,
            average_gold_left=economy.average_gold_left,
            level_8_rate=economy.level_8_rate,
            level_9_rate=economy.level_9_rate,
            low_level_late_rate=economy.low_level_late_rate,
        )

        recommended_composition = next(
            (
                item
                for item in composition_recommendations
                if item.composition_key
                == most_used.composition_key
            ),
            None,
        )

        if recommended_composition is None:
            recommended_composition = (
                composition_recommendations[0]
                if composition_recommendations
                else None
            )

        return {
            "composition": {
                "matches_analyzed": (
                    composition_history.matches_analyzed
                ),
                "unique_compositions": (
                    composition_history.unique_compositions
                ),
                "diversity_rate": (
                    composition_history.diversity_rate
                ),
                "repetition_rate": (
                    composition_history.repetition_rate
                ),
                "forces_composition": (
                    composition_history.forces_composition
                ),
                "flexibility_label": flexibility_label,
                "flexibility_interpretation": flexibility_interpretation,
                "most_used_composition_key": (
                    most_used.composition_key
                ),
                "most_used_carry_character_id": (
                    most_used.carry_character_id
                ),
                "most_used_matches": (
                    most_used.matches_played
                ),
                "most_used_usage_rate": (
                    most_used.usage_rate
                ),
                "most_used_average_placement": (
                    most_used.average_placement
                ),
                "most_used_top4_rate": (
                    most_used.top4_rate
                ),
                "most_used_win_rate": (
                    most_used.win_rate
                ),
                "most_used_average_contest_score": (
                    most_used.average_contest_score
                ),
                "best_composition_key": (
                    best.composition_key
                ),
                "best_carry_character_id": (
                    best.carry_character_id
                ),
                "best_average_placement": (
                    best.average_placement
                ),
                "best_top4_rate": (
                    best.top4_rate
                ),
                "recommendation_label": (
                    recommended_composition.label
                    if recommended_composition is not None
                    else ""
                ),
                "recommendation_explanation": (
                    recommended_composition.explanation
                    if recommended_composition is not None
                    else ""
                ),
            },
            "contest": {
                "matches_analyzed": (
                    contest_history.matches_analyzed
                ),
                "average_score": (
                    contest_history.average_score
                ),
                "high_contest_rate": (
                    contest_history.high_contest_rate
                ),
                "carry_contest_rate": (
                    contest_history.carry_contest_rate
                ),
                "placement_impact": (
                    contest_history.placement_impact
                ),
                "placement_impact_label": contest_impact_label,
                "placement_impact_interpretation": (
                    contest_impact_interpretation
                ),
                "most_contested_unit_id": (
                    contest_history.most_contested_unit_id
                ),
                "most_contested_trait_name": (
                    contest_history.most_contested_trait_name
                ),
                "latest_carry_character_id": (
                    latest_contest.carry_character_id
                ),
                "latest_carry_contested": (
                    latest_contest.carry_contested
                ),
                "latest_opponents_contesting_carry": (
                    latest_contest.opponents_contesting_carry
                ),
                "latest_contested_unit_ids": list(
                    latest_contest.contested_unit_ids
                ),
                "latest_contested_trait_names": list(
                    latest_contest.contested_trait_names
                ),
                "action": contest_recommendation.action,
                "confidence": (
                    contest_recommendation.confidence
                ),
                "explanation": (
                    contest_recommendation.explanation
                ),
            },
            "economy": {
                "matches_analyzed": (
                    economy.matches_analyzed
                ),
                "score": economy.score,
                "label": economy.label,
                "interpretation": economy_interpretation,
                "average_level": (
                    economy.average_level
                ),
                "average_gold_left": (
                    economy.average_gold_left
                ),
                "average_last_round": (
                    economy.average_last_round
                ),
                "level_8_rate": (
                    economy.level_8_rate
                ),
                "level_9_rate": (
                    economy.level_9_rate
                ),
                "low_level_late_rate": (
                    economy.low_level_late_rate
                ),
                "action": economy_recommendation.action,
                "confidence": (
                    economy_recommendation.confidence
                ),
                "explanation": (
                    economy_recommendation.explanation
                ),
            },
        }
