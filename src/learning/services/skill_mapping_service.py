"""
Serviço responsável por converter avaliações de métricas
em avaliações de competências do jogador.
"""

from src.learning.knowledge import get_skill
from src.learning.models import (
    SkillAssessment,
    SkillLevel,
)
from src.performance_engine.models import (
    MetricEvaluation,
    MetricType,
    Performance,
)


class SkillMappingService:
    """
    Converte métricas técnicas do Performance Engine
    em competências compreensíveis para o jogador.

    O serviço não cria métricas novas e não acessa a Riot API.
    """

    @classmethod
    def assess(
        cls,
        *,
        performance: Performance,
    ) -> tuple[SkillAssessment, ...]:
        """
        Avalia as Skills suportadas pelas métricas atuais.

        Args:
            performance:
                Resultado completo do Performance Engine.

        Returns:
            Avaliações de Skills ordenadas do menor score
            para o maior.
        """

        evaluations = {
            evaluation.metric: evaluation
            for evaluation in performance.evaluations
        }

        assessments = (
            cls._assess_economy(),
            cls._assess_leveling(evaluations),
            cls._assess_board_pressure(evaluations),
            cls._assess_consistency(evaluations),
        )

        return tuple(
            sorted(
                assessments,
                key=cls._assessment_order,
            )
        )

    @staticmethod
    def _assess_economy() -> SkillAssessment:
        """
        Economia ainda não possui evidência direta suficiente.

        Nível e dano podem sofrer influência da economia,
        mas não comprovam isoladamente a qualidade dessa Skill.
        """

        return SkillAssessment(
            skill=get_skill("economy"),
            score=0.0,
            level=SkillLevel.NOT_EVALUATED,
            confidence=0.0,
            evidence_metric_ids=(),
            limitations=(
                (
                    "O sistema ainda não possui métricas diretas "
                    "sobre ouro, juros, frequência de reroll ou "
                    "momento dos investimentos."
                ),
                (
                    "Nível e pressão de tabuleiro podem ser afetados "
                    "pela economia, mas não são evidência suficiente "
                    "para avaliar essa competência isoladamente."
                ),
            ),
        )

    @classmethod
    def _assess_leveling(
        cls,
        evaluations: dict[MetricType, MetricEvaluation],
    ) -> SkillAssessment:
        evaluation = evaluations.get(
            MetricType.LEVEL
        )

        if evaluation is None:
            return cls._not_evaluated(
                skill_id="leveling",
                limitation=(
                    "A avaliação de nível não foi disponibilizada "
                    "pelo Performance Engine."
                ),
            )

        score = evaluation.score

        return SkillAssessment(
            skill=get_skill("leveling"),
            score=score,
            level=cls._score_to_level(score),
            confidence=90.0,
            evidence_metric_ids=(
                evaluation.metric.value,
            ),
            limitations=(
                (
                    "O nível médio indica o resultado da progressão, "
                    "mas não revela em quais rodadas o jogador "
                    "comprou experiência."
                ),
            ),
        )

    @classmethod
    def _assess_board_pressure(
        cls,
        evaluations: dict[MetricType, MetricEvaluation],
    ) -> SkillAssessment:
        damage = evaluations.get(
            MetricType.DAMAGE_TO_PLAYERS
        )

        eliminations = evaluations.get(
            MetricType.PLAYERS_ELIMINATED
        )

        available = tuple(
            evaluation
            for evaluation in (
                damage,
                eliminations,
            )
            if evaluation is not None
        )

        if not available:
            return cls._not_evaluated(
                skill_id="board_pressure",
                limitation=(
                    "As métricas de dano e eliminações não foram "
                    "disponibilizadas pelo Performance Engine."
                ),
            )

        total_weight = sum(
            evaluation.weight
            for evaluation in available
        )

        if total_weight <= 0:
            score = sum(
                evaluation.score
                for evaluation in available
            ) / len(available)
        else:
            score = sum(
                evaluation.score * evaluation.weight
                for evaluation in available
            ) / total_weight

        confidence = (
            90.0
            if len(available) == 2
            else 60.0
        )

        limitations = [
            (
                "Dano e eliminações são resultados do tabuleiro e "
                "não identificam diretamente a decisão que gerou "
                "a pressão."
            ),
        ]

        if len(available) < 2:
            limitations.append(
                (
                    "A avaliação utiliza apenas uma das duas "
                    "métricas previstas para esta Skill."
                )
            )

        return SkillAssessment(
            skill=get_skill("board_pressure"),
            score=score,
            level=cls._score_to_level(score),
            confidence=confidence,
            evidence_metric_ids=tuple(
                evaluation.metric.value
                for evaluation in available
            ),
            limitations=tuple(limitations),
        )

    @classmethod
    def _assess_consistency(
        cls,
        evaluations: dict[MetricType, MetricEvaluation],
    ) -> SkillAssessment:
        evaluation = evaluations.get(
            MetricType.CONSISTENCY
        )

        if evaluation is None:
            return cls._not_evaluated(
                skill_id="consistency",
                limitation=(
                    "A avaliação de consistência não foi "
                    "disponibilizada pelo Performance Engine."
                ),
            )

        score = evaluation.score

        return SkillAssessment(
            skill=get_skill("consistency"),
            score=score,
            level=cls._score_to_level(score),
            confidence=80.0,
            evidence_metric_ids=(
                evaluation.metric.value,
            ),
            limitations=(
                (
                    "O desvio de colocação mede oscilação entre "
                    "resultados, mas não identifica sozinho as "
                    "decisões responsáveis por essa variação."
                ),
            ),
        )

    @staticmethod
    def _score_to_level(
        score: float,
    ) -> SkillLevel:
        """
        Converte um score de 0 a 100 em nível visual de Skill.

        As faixas poderão ser calibradas futuramente
        com dados de mais jogadores.
        """

        if score < 20.0:
            return SkillLevel.BEGINNER

        if score < 40.0:
            return SkillLevel.DEVELOPING

        if score < 60.0:
            return SkillLevel.COMPETENT

        if score < 80.0:
            return SkillLevel.ADVANCED

        return SkillLevel.MASTERED

    @staticmethod
    def _not_evaluated(
        *,
        skill_id: str,
        limitation: str,
    ) -> SkillAssessment:
        return SkillAssessment(
            skill=get_skill(skill_id),
            score=0.0,
            level=SkillLevel.NOT_EVALUATED,
            confidence=0.0,
            evidence_metric_ids=(),
            limitations=(
                limitation,
            ),
        )

    @staticmethod
    def _assessment_order(
        assessment: SkillAssessment,
    ) -> tuple[bool, float]:
        """
        Mantém Skills avaliadas primeiro, ordenadas pelo menor score.

        Skills sem evidência aparecem no final.
        """

        not_evaluated = (
            assessment.level
            == SkillLevel.NOT_EVALUATED
        )

        return (
            not_evaluated,
            assessment.score,
        )