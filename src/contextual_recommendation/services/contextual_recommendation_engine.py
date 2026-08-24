from __future__ import annotations

from src.contextual_recommendation.models.contextual_recommendation import (
    ContextualRecommendation,
)


class ContextualRecommendationEngine:
    """
    Contextual Recommendation V1

    Cruza:
    - Action Signal Engine;
    - contexto competitivo;
    - Coach Fusion;
    - missão/Skill atual.

    O motor NÃO escolhe nova Skill nem nova missão.
    Ele só contextualiza como aplicar a prioridade já escolhida.
    """

    @classmethod
    def build(
        cls,
        *,
        action_signals,
        competitive_context: dict | None,
        coach_fusion: dict | None,
        active_skill_label: str | None,
        mission_title: str | None,
    ) -> ContextualRecommendation:
        competitive_context = competitive_context or {}
        coach_fusion = coach_fusion or {}

        skill = active_skill_label or "foco atual"
        mission = mission_title or "missão atual"

        primary = action_signals.primary

        if primary is None:
            primary_title = f"Continue o foco em {skill}"
            primary_action = (
                f"Mantenha a missão “{mission}” como referência principal "
                "para a próxima partida."
            )
            primary_reason = (
                "Os sinais disponíveis ainda não justificam uma mudança "
                "na forma de abordar o treino."
            )
        else:
            primary_title = primary.title
            primary_action = primary.action
            primary_reason = primary.reason

        group_label = cls._competitive_group_label(
            competitive_context
        )
        spectrum_label = cls._spectrum_label(
            competitive_context
        )

        competitive_text = cls._competitive_text(
            group_label=group_label,
            spectrum_label=spectrum_label,
        )

        problem = str(
            coach_fusion.get(
                "observed_problem",
                coach_fusion.get(
                    "problem_observed",
                    "",
                ),
            )
            or ""
        ).strip()

        training_focus = str(
            coach_fusion.get(
                "training_focus",
                coach_fusion.get(
                    "focus_of_training",
                    "",
                ),
            )
            or ""
        ).strip()

        preserve = str(
            coach_fusion.get(
                "strength_to_preserve",
                coach_fusion.get(
                    "preserve_strength",
                    "",
                ),
            )
            or ""
        ).strip()

        training_context = cls._training_context(
            skill=skill,
            mission=mission,
            problem=problem,
            training_focus=training_focus,
        )

        recommendation = (
            f"{primary_action} "
            f"{competitive_text} "
            f"Não tente corrigir tudo ao mesmo tempo: "
            f"a missão continua sendo “{mission}”."
        )

        why_now = (
            f"{primary_reason} "
            f"{training_context}"
        ).strip()

        secondary = tuple(
            item.action
            for item in action_signals.secondary
        )[:2]

        preserve_text = (
            preserve
            if preserve
            else None
        )

        return ContextualRecommendation(
            title=primary_title,
            recommendation=recommendation.strip(),
            why_now=why_now,
            competitive_context=competitive_text,
            training_context=training_context,
            preserve=preserve_text,
            secondary_actions=secondary,
            changes_learning_priority=False,
            changes_mission=False,
            changes_difficulty=False,
            changes_evidence_class=False,
            counts_as_mission_evidence=False,
            predicts_rank_up=False,
        )

    @staticmethod
    def _competitive_group_label(
        competitive_context: dict,
    ) -> str:
        value = (
            competitive_context.get("group_label")
            or competitive_context.get("competitive_group")
            or competitive_context.get("benchmark_name")
            or ""
        )
        return str(value).strip()

    @staticmethod
    def _spectrum_label(
        competitive_context: dict,
    ) -> str:
        value = (
            competitive_context.get("spectrum_band")
            or competitive_context.get("band")
            or competitive_context.get("stage")
            or ""
        )
        return str(value).strip()

    @staticmethod
    def _competitive_text(
        *,
        group_label: str,
        spectrum_label: str,
    ) -> str:
        if group_label and spectrum_label:
            return (
                f"Como você está na faixa {spectrum_label} do grupo "
                f"{group_label}, use esse sinal como contexto do treino, "
                "não como requisito de promoção."
            )

        if group_label:
            return (
                f"Use o grupo {group_label} apenas como contexto competitivo, "
                "não como uma lista de requisitos que você precisa superar."
            )

        if spectrum_label:
            return (
                f"Sua posição atual no espectro é {spectrum_label}; "
                "isso contextualiza o treino sem prever promoção."
            )

        return (
            "Use seu contexto competitivo apenas para ajustar a leitura, "
            "não para transformar métricas em requisitos de subida."
        )

    @staticmethod
    def _training_context(
        *,
        skill: str,
        mission: str,
        problem: str,
        training_focus: str,
    ) -> str:
        parts = [
            f"O foco pedagógico permanece em {skill}.",
            f"A missão ativa continua sendo “{mission}”.",
        ]

        if problem:
            parts.append(
                f"O Coach observou: {problem}."
            )

        if training_focus:
            parts.append(
                f"O foco operacional atual é: {training_focus}."
            )

        return " ".join(parts)
