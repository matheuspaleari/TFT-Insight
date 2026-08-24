from __future__ import annotations

from src.learning.models.learning_priority import (
    LearningPriority,
    LearningPriorityPlan,
)
from src.learning.models.skill_fusion_result import (
    SkillFusionResult,
)
from src.learning.models.skill_level import SkillLevel


class LearningPriorityEngine:
    """
    Ordena Skills para treinamento a partir da Skill Evidence Fusion.

    Princípios:
    - Skills oficiais avaliadas têm prioridade sobre Skills candidatas;
    - Skills NOT_EVALUATED não viram prioridade de treino;
    - contexto não avaliável nunca vira deficiência;
    - evidência histórica positiva pode refinar o foco, mas não apagar
      um gap oficial;
    - strengths são preservadas, não convertidas em problemas;
    - o score de prioridade é estritamente interno.
    """

    @classmethod
    def build(
        cls,
        *,
        fusion_results: tuple[SkillFusionResult, ...],
        max_secondary: int = 2,
        max_strengths: int = 2,
    ) -> LearningPriorityPlan:
        trainable: list[LearningPriority] = []
        strengths: list[LearningPriority] = []
        context: list[LearningPriority] = []

        for result in fusion_results:
            classified = cls._classify(
                result
            )

            if classified is None:
                continue

            if classified.role == "training":
                trainable.append(
                    classified
                )
            elif classified.role == "strength":
                strengths.append(
                    classified
                )
            else:
                context.append(
                    classified
                )

        trainable.sort(
            key=lambda item: (
                -item.internal_score,
                -item.confidence,
                item.skill_id,
            )
        )

        strengths.sort(
            key=lambda item: (
                -item.internal_score,
                -item.confidence,
                item.skill_id,
            )
        )

        context.sort(
            key=lambda item: (
                -item.confidence,
                item.skill_id,
            )
        )

        ranked_training = tuple(
            cls._with_rank(
                item,
                rank=index,
            )
            for index, item in enumerate(
                trainable,
                start=1,
            )
        )

        ranked_strengths = tuple(
            cls._with_rank(
                item,
                rank=index,
            )
            for index, item in enumerate(
                strengths[:max_strengths],
                start=1,
            )
        )

        ranked_context = tuple(
            cls._with_rank(
                item,
                rank=index,
            )
            for index, item in enumerate(
                context,
                start=1,
            )
        )

        primary = (
            ranked_training[0]
            if ranked_training
            else None
        )

        secondary = (
            ranked_training[
                1 : 1 + max_secondary
            ]
            if ranked_training
            else ()
        )

        return LearningPriorityPlan(
            primary=primary,
            secondary=tuple(
                secondary
            ),
            strengths=ranked_strengths,
            context=ranked_context,
        )

    @classmethod
    def _classify(
        cls,
        result: SkillFusionResult,
    ) -> LearningPriority | None:
        habit_ids = tuple(
            dict.fromkeys(
                habit_id
                for signal in result.supporting_signals
                for habit_id in signal.habit_ids
            )
        )

        positive_support = any(
            signal.direction == "positive"
            for signal in result.supporting_signals
        )

        negative_support = any(
            signal.direction == "negative"
            for signal in result.supporting_signals
        )

        if (
            result.decision
            == "candidate_context"
        ):
            return LearningPriority(
                skill_id=result.skill_id,
                skill_label=result.skill_label,
                role="context",
                rank=0,
                internal_score=0.0,
                confidence=cls._confidence(
                    result
                ),
                training_focus=(
                    "Observar mais antes de transformar este sinal "
                    "em objetivo de treino."
                ),
                reason=(
                    "Há contexto histórico relevante, mas os dados atuais "
                    "não permitem avaliar domínio da Skill."
                ),
                evidence_status="context_only",
                source_decision=result.decision,
                habit_ids=habit_ids,
                limitations=result.limitations,
            )

        if (
            result.baseline_available
            and result.fused_level
            == SkillLevel.NOT_EVALUATED
        ):
            return LearningPriority(
                skill_id=result.skill_id,
                skill_label=result.skill_label,
                role="context",
                rank=0,
                internal_score=0.0,
                confidence=cls._confidence(
                    result
                ),
                training_focus=(
                    "Coletar evidências mais diretas antes de prescrever treino."
                ),
                reason=(
                    "A Skill existe no catálogo, mas ainda não possui "
                    "evidência suficiente para uma avaliação confiável."
                ),
                evidence_status="not_evaluated",
                source_decision=result.decision,
                habit_ids=habit_ids,
                limitations=result.limitations,
            )

        if (
            result.decision
            == "candidate_skill"
        ):
            level = result.fused_level

            if level is None:
                return None

            if level >= SkillLevel.ADVANCED:
                return LearningPriority(
                    skill_id=result.skill_id,
                    skill_label=result.skill_label,
                    role="strength",
                    rank=0,
                    internal_score=cls._strength_score(
                        result
                    ),
                    confidence=cls._confidence(
                        result
                    ),
                    training_focus=(
                        "Preservar este padrão enquanto o foco principal "
                        "fica nas Skills oficiais com gap."
                    ),
                    reason=(
                        "A evidência histórica sugere uma capacidade forte, "
                        "mas a Skill ainda é candidata ao catálogo."
                    ),
                    evidence_status="candidate",
                    source_decision=result.decision,
                    habit_ids=habit_ids,
                    limitations=result.limitations,
                )

            return LearningPriority(
                skill_id=result.skill_id,
                skill_label=result.skill_label,
                role="context",
                rank=0,
                internal_score=0.0,
                confidence=cls._confidence(
                    result
                ),
                training_focus=(
                    "Acompanhar a Skill candidata antes de usá-la como "
                    "prioridade oficial de treino."
                ),
                reason=(
                    "Existe sinal avaliável, mas ainda não há assessment "
                    "oficial desta Skill no catálogo."
                ),
                evidence_status="candidate",
                source_decision=result.decision,
                habit_ids=habit_ids,
                limitations=result.limitations,
            )

        level = result.fused_level

        if level is None:
            return None

        if level >= SkillLevel.ADVANCED:
            return LearningPriority(
                skill_id=result.skill_id,
                skill_label=result.skill_label,
                role="strength",
                rank=0,
                internal_score=cls._strength_score(
                    result
                ),
                confidence=cls._confidence(
                    result
                ),
                training_focus=(
                    "Preservar esta força enquanto trabalha nas prioridades "
                    "de desenvolvimento."
                ),
                reason=(
                    "A Skill possui avaliação oficial forte e não deve ser "
                    "convertida artificialmente em prioridade de correção."
                ),
                evidence_status="official",
                source_decision=result.decision,
                habit_ids=habit_ids,
                limitations=result.limitations,
            )

        score = cls._training_score(
            result=result,
            positive_support=positive_support,
            negative_support=negative_support,
        )

        training_focus = cls._training_focus(
            result=result,
            positive_support=positive_support,
            negative_support=negative_support,
        )

        reason = cls._training_reason(
            result=result,
            positive_support=positive_support,
            negative_support=negative_support,
        )

        return LearningPriority(
            skill_id=result.skill_id,
            skill_label=result.skill_label,
            role="training",
            rank=0,
            internal_score=score,
            confidence=cls._confidence(
                result
            ),
            training_focus=training_focus,
            reason=reason,
            evidence_status="official",
            source_decision=result.decision,
            habit_ids=habit_ids,
            limitations=result.limitations,
        )

    @classmethod
    def _training_score(
        cls,
        *,
        result: SkillFusionResult,
        positive_support: bool,
        negative_support: bool,
    ) -> float:
        """
        Score interno de ordenação.

        Base:
        - gap oficial: quanto menor o score, maior a urgência;
        - confiança oficial: aumenta força da conclusão;
        - evidência negativa histórica: aumenta urgência;
        - evidência positiva histórica: reduz levemente a urgência,
          mas nunca elimina um gap oficial.
        """
        official_score = (
            result.fused_score
            if result.fused_score is not None
            else 50.0
        )

        confidence = cls._confidence(
            result
        )

        gap_component = max(
            0.0,
            100.0 - official_score,
        )

        confidence_component = (
            confidence * 0.20
        )

        history_adjustment = 0.0

        if negative_support:
            history_adjustment += 10.0

        if positive_support:
            history_adjustment -= 6.0

        if (
            result.decision
            == "evidence_disagreement"
        ):
            history_adjustment -= 4.0

        return round(
            max(
                0.0,
                min(
                    120.0,
                    gap_component
                    + confidence_component
                    + history_adjustment,
                ),
            ),
            2,
        )

    @staticmethod
    def _training_focus(
        *,
        result: SkillFusionResult,
        positive_support: bool,
        negative_support: bool,
    ) -> str:
        if (
            result.skill_id == "leveling"
            and positive_support
        ):
            return (
                "Refinar o ritmo e o timing da progressão de nível, "
                "em vez de simplesmente tentar chegar a níveis mais altos."
            )

        if negative_support:
            return (
                "Treinar o ponto fraco oficial dando atenção especial ao "
                "padrão negativo recorrente observado no histórico."
            )

        if result.skill_id == "consistency":
            return (
                "Aumentar a regularidade das decisões que transformam "
                "partidas em resultados estáveis."
            )

        if result.skill_id == "board_pressure":
            return (
                "Melhorar a capacidade de converter o tabuleiro em pressão "
                "consistente sobre os adversários."
            )

        return (
            "Trabalhar esta Skill de forma isolada nas próximas partidas "
            "e acompanhar a evolução contra o benchmark."
        )

    @staticmethod
    def _training_reason(
        *,
        result: SkillFusionResult,
        positive_support: bool,
        negative_support: bool,
    ) -> str:
        level_name = (
            result.fused_level.name
            if result.fused_level is not None
            else "UNKNOWN"
        )

        if positive_support:
            return (
                f"A avaliação oficial da Skill está em {level_name}, "
                "mas existe uma base histórica positiva. O treino deve "
                "atacar o gap específico sem apagar o que já funciona."
            )

        if negative_support:
            return (
                f"A avaliação oficial da Skill está em {level_name} e o "
                "histórico também contém evidência negativa recorrente."
            )

        return (
            f"A avaliação oficial da Skill está em {level_name} e ainda "
            "há espaço relevante de desenvolvimento contra a referência."
        )

    @staticmethod
    def _strength_score(
        result: SkillFusionResult,
    ) -> float:
        score = (
            result.fused_score
            if result.fused_score is not None
            else 0.0
        )

        confidence = (
            result.fused_confidence
            if result.fused_confidence is not None
            else 0.0
        )

        return round(
            score + confidence * 0.10,
            2,
        )

    @staticmethod
    def _confidence(
        result: SkillFusionResult,
    ) -> float:
        value = (
            result.fused_confidence
            if result.fused_confidence is not None
            else result.baseline_confidence
        )

        if value is None:
            return 0.0

        return round(
            max(
                0.0,
                min(
                    100.0,
                    float(value),
                ),
            ),
            2,
        )

    @staticmethod
    def _with_rank(
        item: LearningPriority,
        *,
        rank: int,
    ) -> LearningPriority:
        return LearningPriority(
            skill_id=item.skill_id,
            skill_label=item.skill_label,
            role=item.role,
            rank=rank,
            internal_score=item.internal_score,
            confidence=item.confidence,
            training_focus=item.training_focus,
            reason=item.reason,
            evidence_status=item.evidence_status,
            source_decision=item.source_decision,
            habit_ids=item.habit_ids,
            limitations=item.limitations,
        )
