from __future__ import annotations

from src.coach_intelligence.models.adaptive_coaching_strategy import (
    AdaptiveCoachingStrategy,
)


class AdaptiveCoachingStrategyEngine:
    """
    Fase 11.5.

    Decide a ESTRATÉGIA pedagógica para a Skill que já foi escolhida
    pelo Learning Priority.

    Este engine NÃO escolhe outra Skill e NÃO cria missão.
    """

    LEVEL_ORDER = {
        "NOT_EVALUATED": 0,
        "BEGINNER": 1,
        "DEVELOPING": 2,
        "COMPETENT": 3,
        "ADVANCED": 4,
        "MASTERED": 5,
    }

    @classmethod
    def decide(
        cls,
        *,
        foundation: dict,
        priority_skill_id: str,
        current_task_id: str | None,
    ) -> AdaptiveCoachingStrategy:
        profile = (
            foundation.get(
                "profile",
                {}
            )
            if isinstance(
                foundation,
                dict,
            )
            else {}
        )

        skills = profile.get(
            "skills",
            {}
        )

        if not isinstance(
            skills,
            dict,
        ):
            skills = {}

        skill = skills.get(
            priority_skill_id,
            {},
        )

        if not isinstance(
            skill,
            dict,
        ):
            skill = {}

        trend = str(
            skill.get(
                "trend",
                "INSUFFICIENT_HISTORY",
            )
        ).upper()

        level = str(
            skill.get(
                "level",
                "NOT_EVALUATED",
            )
        ).upper()

        score = skill.get(
            "score"
        )

        if score is not None:
            score = float(
                score
            )

        difficulty = skill.get(
            "current_difficulty"
        )

        anti_loop = str(
            skill.get(
                "anti_loop_action",
                "CONTINUE",
            )
        ).upper()

        progression = str(
            skill.get(
                "task_progression",
                "HOLD",
            )
        ).upper()

        effectiveness = cls._task_effectiveness(
            foundation=foundation,
            skill_id=priority_skill_id,
            task_id=current_task_id,
        )

        strategy, confidence, rationale = cls._classify(
            level=level,
            trend=trend,
            difficulty=difficulty,
            anti_loop=anti_loop,
            progression=progression,
            effectiveness=effectiveness,
        )

        return AdaptiveCoachingStrategy(
            priority_skill_id=priority_skill_id,
            strategy=strategy,
            confidence=confidence,
            current_level=level,
            current_score=score,
            training_trend=trend,
            current_difficulty=(
                str(difficulty).upper()
                if difficulty
                else None
            ),
            current_task_id=current_task_id,
            task_effectiveness=effectiveness,
            anti_loop_action=anti_loop,
            rationale=rationale,
            safeguards=(
                "Learning Priority continua responsável por escolher a Skill.",
                "A estratégia adapta somente a abordagem de treino da Skill recebida.",
                "Efetividade e relações históricas não são tratadas como causalidade.",
            ),
        )

    @classmethod
    def _classify(
        cls,
        *,
        level: str,
        trend: str,
        difficulty,
        anti_loop: str,
        progression: str,
        effectiveness: str,
    ) -> tuple[str, str, str]:
        if anti_loop in {
            "REASSESS",
            "COOLDOWN_SKILL",
        }:
            return (
                "CHANGE_APPROACH",
                "HIGH"
                if anti_loop == "COOLDOWN_SKILL"
                else "MODERATE",
                (
                    "O histórico acionou uma proteção anti-loop. "
                    "A prioridade é preservada, mas repetir a mesma abordagem "
                    "não é recomendado."
                ),
            )

        if effectiveness == "LOW_OBSERVED_EFFECTIVENESS":
            return (
                "CHANGE_APPROACH",
                "MODERATE",
                (
                    "O exercício atual acumulou resultados observados "
                    "predominantemente negativos. A Skill continua sendo o foco, "
                    "mas a abordagem deve mudar."
                ),
            )

        if (
            trend == "IMPROVING"
            and progression == "ADVANCE_CANDIDATE"
        ):
            return (
                "CHALLENGE",
                "MODERATE",
                (
                    "A Skill apresenta tendência de melhora e o Learning Loop "
                    "já sinalizou candidatura a progressão de dificuldade."
                ),
            )

        if (
            trend == "STABLE"
            or effectiveness == "STABLE_EFFECT"
        ):
            return (
                "CONSOLIDATE",
                "MODERATE",
                (
                    "Os sinais recentes estão estáveis. O melhor próximo passo "
                    "é consolidar a execução antes de elevar a exigência."
                ),
            )

        if (
            level in {
                "BEGINNER",
                "DEVELOPING",
            }
            or str(
                difficulty or ""
            ).upper() == "FOUNDATION"
            or trend == "INSUFFICIENT_HISTORY"
        ):
            return (
                "BUILD_FOUNDATION",
                "LOW"
                if trend == "INSUFFICIENT_HISTORY"
                else "MODERATE",
                (
                    "O perfil atual ainda pede fundamentos ou possui histórico "
                    "insuficiente para justificar uma estratégia mais agressiva."
                ),
            )

        return (
            "MAINTAIN",
            "LOW",
            (
                "Não há sinal forte para mudar a abordagem atual. "
                "A estratégia mantém o plano e continua coletando evidências."
            ),
        )

    @staticmethod
    def _task_effectiveness(
        *,
        foundation: dict,
        skill_id: str,
        task_id: str | None,
    ) -> str:
        if not task_id:
            return "INSUFFICIENT_HISTORY"

        items = foundation.get(
            "training_effectiveness",
            [],
        )

        if not isinstance(
            items,
            list,
        ):
            return "INSUFFICIENT_HISTORY"

        for item in items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                item.get(
                    "skill_id"
                )
                == skill_id
                and item.get(
                    "task_id"
                )
                == task_id
            ):
                return str(
                    item.get(
                        "effectiveness",
                        "INSUFFICIENT_HISTORY",
                    )
                ).upper()

        return "INSUFFICIENT_HISTORY"
