from src.decision_engine.models import (
    ContestHistoryReport,
    FlexReport,
    StrategicReport,
)

from src.recommendation_engine.models import (
    ImprovementPriorityReport,
    ImprovementRecommendation,
    RecommendationCategory,
    RecommendationPriority,
)


class ImprovementPriorityEngine:
    """
    Ordena oportunidades pelo ganho esperado.

    Impact score:
    - distância até 100;
    - peso estratégico;
    - evidência de impacto em colocação;
    - confiança da amostra.

    expected_placement_gain é uma estimativa heurística e não causal.
    """

    WEIGHTS = {
        RecommendationCategory.ITEMIZATION: 1.00,
        RecommendationCategory.CONTEST: 0.95,
        RecommendationCategory.ECONOMY: 0.80,
        RecommendationCategory.TEMPO: 0.75,
        RecommendationCategory.FLEX: 0.60,
    }

    @classmethod
    def analyze(
        cls,
        *,
        strategic_report: StrategicReport,
        contest_history: ContestHistoryReport,
        flex_report: FlexReport,
    ) -> ImprovementPriorityReport:
        candidates = [
            cls._build(
                recommendation_id="improve_itemization",
                category=RecommendationCategory.ITEMIZATION,
                score=strategic_report.itemization.score,
                confidence=90.0,
                title="Complete carry e tank com mais consistência",
                action=(
                    "Priorize três itens no carry principal e no tank "
                    "antes de espalhar recursos em unidades secundárias."
                ),
                evidence=(
                    (
                        "Carry com três itens: "
                        f"{strategic_report.itemization.carry_full_item_rate:.1f}%"
                    ),
                    (
                        "Tank com três itens: "
                        f"{strategic_report.itemization.tank_full_item_rate:.1f}%"
                    ),
                ),
            ),
            cls._build(
                recommendation_id="reduce_contest",
                category=RecommendationCategory.CONTEST,
                score=max(
                    0.0,
                    100.0 - contest_history.average_score,
                ),
                confidence=85.0,
                title="Reduza disputas diretas pelo carry",
                action=(
                    "Quando dois ou mais adversários disputarem o carry, "
                    "prepare uma linha alternativa ou faça o pivot."
                ),
                evidence=(
                    (
                        "Carry contestado: "
                        f"{contest_history.carry_contest_rate:.1f}%"
                    ),
                    (
                        "Contestação alta/extrema: "
                        f"{contest_history.high_contest_rate:.1f}%"
                    ),
                    (
                        "Impacto observado: "
                        f"{contest_history.placement_impact:+.2f}"
                        if contest_history.placement_impact is not None
                        else "Impacto observado: indisponível"
                    ),
                ),
                placement_impact=contest_history.placement_impact,
            ),
            cls._build(
                recommendation_id="improve_economy",
                category=RecommendationCategory.ECONOMY,
                score=strategic_report.economy.score,
                confidence=75.0,
                title="Converta economia no momento correto",
                action=(
                    "Evite terminar partidas longas em nível baixo e "
                    "revise derrotas com muito ouro restante."
                ),
                evidence=(
                    (
                        "Nível 8: "
                        f"{strategic_report.economy.level_8_rate:.1f}%"
                    ),
                    (
                        "Nível 9: "
                        f"{strategic_report.economy.level_9_rate:.1f}%"
                    ),
                    (
                        "Partidas longas em nível baixo: "
                        f"{strategic_report.economy.low_level_late_rate:.1f}%"
                    ),
                ),
            ),
            cls._build(
                recommendation_id="improve_tempo",
                category=RecommendationCategory.TEMPO,
                score=strategic_report.tempo.score,
                confidence=75.0,
                title="Estabilize a transição para o late game",
                action=(
                    "Revise partidas em que o tabuleiro não estabilizou "
                    "antes do estágio final."
                ),
                evidence=(
                    (
                        "Late game: "
                        f"{strategic_report.tempo.late_game_rate:.1f}%"
                    ),
                    (
                        "Saídas precoces: "
                        f"{strategic_report.tempo.early_exit_rate:.1f}%"
                    ),
                ),
            ),
            cls._build(
                recommendation_id="increase_flex",
                category=RecommendationCategory.FLEX,
                score=flex_report.score,
                confidence=80.0,
                title="Amplie as linhas de adaptação",
                action=(
                    "Mantenha pelo menos uma alternativa de carry e "
                    "frontline quando a composição principal estiver fechada."
                ),
                evidence=(
                    (
                        "Composições únicas: "
                        f"{flex_report.unique_compositions}"
                    ),
                    (
                        "Taxa de repetição: "
                        f"{flex_report.repetition_rate:.1f}%"
                    ),
                ),
            ),
        ]

        relevant = tuple(
            sorted(
                (
                    item
                    for item in candidates
                    if item.current_score < 80.0
                ),
                key=lambda item: (
                    item.impact_score,
                    item.confidence,
                ),
                reverse=True,
            )
        )

        strongest = max(
            candidates,
            key=lambda item: item.current_score,
        )

        summary = (
            (
                f"A prioridade principal é "
                f"{relevant[0].category.value.lower()}: "
                f"{relevant[0].title.lower()}."
            )
            if relevant
            else (
                "Nenhuma área crítica foi encontrada; "
                "o foco deve ser refinamento."
            )
        )

        return ImprovementPriorityReport(
            recommendations=relevant,
            strongest_area=strongest.category.value,
            summary=summary,
        )

    @classmethod
    def _build(
        cls,
        *,
        recommendation_id: str,
        category: RecommendationCategory,
        score: float,
        confidence: float,
        title: str,
        action: str,
        evidence: tuple[str, ...],
        placement_impact: float | None = None,
    ) -> ImprovementRecommendation:
        gap = 100.0 - score
        weight = cls.WEIGHTS[category]

        impact_bonus = (
            min(abs(placement_impact), 3.0) / 3.0 * 20.0
            if placement_impact is not None
            else 0.0
        )

        impact_score = min(
            100.0,
            gap * weight + impact_bonus,
        )

        if impact_score >= 65.0:
            priority = RecommendationPriority.CRITICAL
        elif impact_score >= 45.0:
            priority = RecommendationPriority.HIGH
        elif impact_score >= 25.0:
            priority = RecommendationPriority.MEDIUM
        else:
            priority = RecommendationPriority.LOW

        expected_gain = min(
            1.5,
            impact_score / 100.0 * 1.2,
        )

        return ImprovementRecommendation(
            recommendation_id=recommendation_id,
            category=category,
            priority=priority,
            title=title,
            action=action,
            current_score=round(score, 2),
            impact_score=round(impact_score, 2),
            confidence=round(confidence, 2),
            expected_placement_gain=round(
                expected_gain,
                2,
            ),
            evidence=evidence,
        )
