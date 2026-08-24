from __future__ import annotations

from src.decision_engine.models import (
    CompositionHistoryReport,
    ContestHistoryReport,
    DecisionExplanationReport,
    ExplanationFactor,
    ExplanationImpact,
    FlexReport,
    StrategicReport,
)


class DecisionExplanationEngine:
    """
    Converte relatórios técnicos em diagnóstico histórico explicável.

    Faixas:
    - 80 a 100: muito forte;
    - 70 a 79: positivo;
    - 55 a 69: neutro;
    - 40 a 54: atenção;
    - abaixo de 40: crítico.
    """

    ECONOMY_WEIGHT = 0.25
    ITEMIZATION_WEIGHT = 0.30
    TEMPO_WEIGHT = 0.20
    CONTEST_WEIGHT = 0.15
    FLEX_WEIGHT = 0.10

    VERY_STRONG_THRESHOLD = 80.0
    POSITIVE_THRESHOLD = 70.0
    NEUTRAL_THRESHOLD = 55.0
    ATTENTION_THRESHOLD = 40.0

    @classmethod
    def explain(
        cls,
        *,
        strategic_report: StrategicReport,
        contest_history: ContestHistoryReport | None = None,
        flex_report: FlexReport | None = None,
        composition_history: CompositionHistoryReport | None = None,
    ) -> DecisionExplanationReport:
        factors = [
            cls._economy_factor(strategic_report),
            cls._itemization_factor(strategic_report),
            cls._tempo_factor(strategic_report),
            cls._contest_factor(contest_history),
            cls._flex_factor(flex_report),
            cls._augment_factor(strategic_report),
            cls._positioning_factor(strategic_report),
        ]

        weighted = [
            factor
            for factor in factors
            if (
                factor.score is not None
                and factor.weight > 0.0
                and factor.impact
                != ExplanationImpact.UNAVAILABLE
            )
        ]

        total_weight = sum(
            factor.weight
            for factor in weighted
        )

        overall_score = (
            sum(
                factor.score * factor.weight
                for factor in weighted
                if factor.score is not None
            )
            / total_weight
            if total_weight > 0.0
            else strategic_report.overall_score
        )

        normalized = tuple(
            cls._normalize_factor(
                factor=factor,
                total_weight=total_weight,
            )
            for factor in factors
        )

        positive = tuple(
            sorted(
                (
                    factor
                    for factor in normalized
                    if factor.impact
                    == ExplanationImpact.POSITIVE
                ),
                key=lambda factor: (
                    factor.score
                    if factor.score is not None
                    else -1.0
                ),
                reverse=True,
            )
        )

        negative = tuple(
            sorted(
                (
                    factor
                    for factor in normalized
                    if factor.impact
                    == ExplanationImpact.NEGATIVE
                ),
                key=lambda factor: (
                    factor.score
                    if factor.score is not None
                    else 100.0
                ),
            )
        )

        neutral = tuple(
            sorted(
                (
                    factor
                    for factor in normalized
                    if factor.impact
                    == ExplanationImpact.NEUTRAL
                ),
                key=lambda factor: (
                    factor.score
                    if factor.score is not None
                    else 100.0
                ),
            )
        )

        unavailable = tuple(
            factor
            for factor in normalized
            if factor.impact
            == ExplanationImpact.UNAVAILABLE
        )

        label = cls._overall_label(overall_score)

        strengths = tuple(
            cls._strength_text(factor)
            for factor in positive[:3]
        )

        priorities = tuple(
            cls._priority_text(factor)
            for factor in negative[:3]
        )

        if not priorities and neutral:
            priorities = tuple(
                cls._neutral_priority_text(factor)
                for factor in neutral[:2]
            )

        caveats = [
            f"{factor.title}: {factor.explanation}"
            for factor in unavailable
        ]

        caveats.append(
            "Economia e tempo são inferidos pelo estado final "
            "das partidas, não por um histórico completo por rodada."
        )

        if (
            composition_history is not None
            and composition_history.matches_analyzed < 20
        ):
            caveats.append(
                "A amostra possui menos de 20 partidas; "
                "trate os padrões como sinais iniciais."
            )

        headline = cls._headline(
            score=overall_score,
            negative=negative,
        )

        summary = cls._summary(
            score=overall_score,
            label=label,
            positive=positive,
            negative=negative,
            neutral=neutral,
            composition_history=composition_history,
        )

        return DecisionExplanationReport(
            overall_score=round(overall_score, 2),
            label=label,
            headline=headline,
            summary=summary,
            positive_factors=positive,
            negative_factors=negative,
            neutral_factors=neutral,
            unavailable_factors=unavailable,
            strengths=strengths,
            priorities=priorities,
            caveats=tuple(caveats),
        )

    @classmethod
    def _factor_impact(
        cls,
        score: float,
    ) -> ExplanationImpact:
        if score >= cls.POSITIVE_THRESHOLD:
            return ExplanationImpact.POSITIVE

        if score >= cls.NEUTRAL_THRESHOLD:
            return ExplanationImpact.NEUTRAL

        return ExplanationImpact.NEGATIVE

    @classmethod
    def _scored_factor(
        cls,
        *,
        factor_id: str,
        title: str,
        score: float,
        weight: float,
        explanation: str,
        evidence: tuple[str, ...],
    ) -> ExplanationFactor:
        return ExplanationFactor(
            factor_id=factor_id,
            title=title,
            impact=cls._factor_impact(score),
            score=round(score, 2),
            weight=weight,
            explanation=explanation,
            evidence=evidence,
        )

    @staticmethod
    def _unavailable(
        *,
        factor_id: str,
        title: str,
        reason: str,
    ) -> ExplanationFactor:
        return ExplanationFactor(
            factor_id=factor_id,
            title=title,
            impact=ExplanationImpact.UNAVAILABLE,
            score=None,
            weight=0.0,
            contribution=0.0,
            explanation=reason,
        )

    @staticmethod
    def _normalize_factor(
        *,
        factor: ExplanationFactor,
        total_weight: float,
    ) -> ExplanationFactor:
        if (
            factor.score is None
            or factor.weight <= 0.0
            or total_weight <= 0.0
        ):
            return factor

        normalized_weight = (
            factor.weight
            / total_weight
        )

        return ExplanationFactor(
            factor_id=factor.factor_id,
            title=factor.title,
            impact=factor.impact,
            score=factor.score,
            weight=round(normalized_weight, 4),
            contribution=round(
                factor.score
                * normalized_weight,
                2,
            ),
            explanation=factor.explanation,
            evidence=factor.evidence,
        )

    @classmethod
    def _economy_factor(
        cls,
        strategic_report: StrategicReport,
    ) -> ExplanationFactor:
        report = strategic_report.economy

        if not report.availability.available:
            return cls._unavailable(
                factor_id="economy",
                title="Economia",
                reason=report.availability.reason,
            )

        return cls._scored_factor(
            factor_id="economy",
            title="Economia",
            score=report.score,
            weight=cls.ECONOMY_WEIGHT,
            explanation=report.summary,
            evidence=(
                f"Nível médio: {report.average_level:.2f}",
                f"Nível 8: {report.level_8_rate:.1f}%",
                f"Nível 9: {report.level_9_rate:.1f}%",
                (
                    "Partidas longas em nível baixo: "
                    f"{report.low_level_late_rate:.1f}%"
                ),
            ),
        )

    @classmethod
    def _itemization_factor(
        cls,
        strategic_report: StrategicReport,
    ) -> ExplanationFactor:
        report = strategic_report.itemization

        if not report.availability.available:
            return cls._unavailable(
                factor_id="itemization",
                title="Itemização",
                reason=report.availability.reason,
            )

        return cls._scored_factor(
            factor_id="itemization",
            title="Itemização",
            score=report.score,
            weight=cls.ITEMIZATION_WEIGHT,
            explanation=report.summary,
            evidence=(
                (
                    "Carry com três itens: "
                    f"{report.carry_full_item_rate:.1f}%"
                ),
                (
                    "Tank com três itens: "
                    f"{report.tank_full_item_rate:.1f}%"
                ),
                (
                    "Itens em papéis desconhecidos: "
                    f"{report.unknown_item_share:.1f}%"
                ),
            ),
        )

    @classmethod
    def _tempo_factor(
        cls,
        strategic_report: StrategicReport,
    ) -> ExplanationFactor:
        report = strategic_report.tempo

        if not report.availability.available:
            return cls._unavailable(
                factor_id="tempo",
                title="Tempo",
                reason=report.availability.reason,
            )

        return cls._scored_factor(
            factor_id="tempo",
            title="Tempo",
            score=report.score,
            weight=cls.TEMPO_WEIGHT,
            explanation=report.summary,
            evidence=(
                f"Late game: {report.late_game_rate:.1f}%",
                f"Saídas precoces: {report.early_exit_rate:.1f}%",
                (
                    "Dano médio aos jogadores: "
                    f"{report.average_damage_to_players:.1f}"
                ),
            ),
        )

    @classmethod
    def _contest_factor(
        cls,
        contest_history: ContestHistoryReport | None,
    ) -> ExplanationFactor:
        if contest_history is None:
            return cls._unavailable(
                factor_id="contest",
                title="Contestação",
                reason="ContestHistoryReport não fornecido.",
            )

        score = max(
            0.0,
            100.0 - contest_history.average_score,
        )

        if contest_history.high_contest_rate >= 35.0:
            explanation = (
                "A composição aparece contestada com frequência."
            )
        elif contest_history.carry_contest_rate >= 50.0:
            explanation = (
                "O carry é disputado com frequência, mesmo sem "
                "contestação extrema da composição."
            )
        else:
            explanation = (
                "A contestação recente está controlada."
            )

        evidence = (
            (
                "Contestação média: "
                f"{contest_history.average_score:.1f}"
            ),
            (
                "Contestação alta/extrema: "
                f"{contest_history.high_contest_rate:.1f}%"
            ),
            (
                "Carry contestado: "
                f"{contest_history.carry_contest_rate:.1f}%"
            ),
        )

        if contest_history.placement_impact is not None:
            evidence += (
                (
                    "Impacto observado: "
                    f"{contest_history.placement_impact:+.2f}"
                ),
            )

        return cls._scored_factor(
            factor_id="contest",
            title="Contestação",
            score=score,
            weight=cls.CONTEST_WEIGHT,
            explanation=explanation,
            evidence=evidence,
        )

    @classmethod
    def _flex_factor(
        cls,
        flex_report: FlexReport | None,
    ) -> ExplanationFactor:
        if flex_report is None:
            return cls._unavailable(
                factor_id="flex",
                title="Flexibilidade",
                reason="FlexReport não fornecido.",
            )

        if flex_report.likely_forces_composition:
            explanation = (
                "Existe um padrão forte de repetição."
            )
        elif flex_report.score >= 75.0:
            explanation = (
                "O jogador adapta composições e papéis "
                "com boa frequência."
            )
        else:
            explanation = (
                "A flexibilidade é intermediária."
            )

        return cls._scored_factor(
            factor_id="flex",
            title="Flexibilidade",
            score=flex_report.score,
            weight=cls.FLEX_WEIGHT,
            explanation=explanation,
            evidence=(
                (
                    "Composições únicas: "
                    f"{flex_report.unique_compositions}"
                ),
                (
                    "Carries diferentes: "
                    f"{flex_report.unique_carries}"
                ),
                (
                    "Tanks diferentes: "
                    f"{flex_report.unique_tanks}"
                ),
                (
                    "Repetição: "
                    f"{flex_report.repetition_rate:.1f}%"
                ),
            ),
        )

    @classmethod
    def _augment_factor(
        cls,
        strategic_report: StrategicReport,
    ) -> ExplanationFactor:
        report = strategic_report.augment

        if not report.availability.available:
            return cls._unavailable(
                factor_id="augment",
                title="Augments",
                reason=(
                    report.availability.reason
                    or report.summary
                ),
            )

        return ExplanationFactor(
            factor_id="augment",
            title="Augments",
            impact=ExplanationImpact.NEUTRAL,
            score=None,
            weight=0.0,
            explanation=report.summary,
        )

    @classmethod
    def _positioning_factor(
        cls,
        strategic_report: StrategicReport,
    ) -> ExplanationFactor:
        report = strategic_report.positioning

        if not report.availability.available:
            return cls._unavailable(
                factor_id="positioning",
                title="Posicionamento",
                reason=(
                    report.availability.reason
                    or report.summary
                ),
            )

        return ExplanationFactor(
            factor_id="positioning",
            title="Posicionamento",
            impact=ExplanationImpact.NEUTRAL,
            score=None,
            weight=0.0,
            explanation=report.summary,
        )

    @staticmethod
    def _strength_text(
        factor: ExplanationFactor,
    ) -> str:
        return (
            f"{factor.title}: {factor.score:.0f}/100. "
            f"{factor.explanation}"
        )

    @staticmethod
    def _priority_text(
        factor: ExplanationFactor,
    ) -> str:
        prefix = (
            "Corrija"
            if factor.score is not None
            and factor.score < 40.0
            else "Priorize"
        )

        return (
            f"{prefix} {factor.title.lower()}: "
            f"{factor.score:.0f}/100. "
            f"{factor.explanation}"
        )

    @staticmethod
    def _neutral_priority_text(
        factor: ExplanationFactor,
    ) -> str:
        return (
            f"Refine {factor.title.lower()}: "
            f"{factor.score:.0f}/100. "
            f"{factor.explanation}"
        )

    @staticmethod
    def _headline(
        *,
        score: float,
        negative: tuple[ExplanationFactor, ...],
    ) -> str:
        if negative:
            return (
                "A execução possui uma base útil, mas há fatores "
                "que merecem atenção."
            )

        if score >= 80.0:
            return (
                "A execução estratégica recente foi muito forte."
            )

        return (
            "A execução foi boa, sustentada por fatores "
            "estratégicos consistentes."
        )

    @staticmethod
    def _summary(
        *,
        score: float,
        label: str,
        positive: tuple[ExplanationFactor, ...],
        negative: tuple[ExplanationFactor, ...],
        neutral: tuple[ExplanationFactor, ...],
        composition_history: CompositionHistoryReport | None,
    ) -> str:
        sentences = [
            (
                f"A execução estratégica foi classificada como "
                f"{label.lower()}, com nota {score:.1f}/100."
            )
        ]

        if positive:
            names = ", ".join(
                factor.title.lower()
                for factor in positive[:2]
            )
            sentences.append(
                f"Os principais fatores positivos foram {names}."
            )

        if negative:
            names = ", ".join(
                factor.title.lower()
                for factor in negative[:2]
            )
            sentences.append(
                f"Os fatores que mais exigem atenção são {names}."
            )
        elif neutral:
            sentences.append(
                f"O principal espaço de evolução está em "
                f"{neutral[0].title.lower()}."
            )

        if composition_history is not None:
            sentences.append(
                (
                    "Foram identificadas "
                    f"{composition_history.unique_compositions} "
                    "composições estratégicas."
                )
            )

        return " ".join(sentences)

    @staticmethod
    def _overall_label(score: float) -> str:
        if score < 40.0:
            return "Crítica"
        if score < 55.0:
            return "Atenção"
        if score < 70.0:
            return "Regular"
        if score < 80.0:
            return "Boa"
        return "Muito forte"
