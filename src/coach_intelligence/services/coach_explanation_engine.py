from __future__ import annotations

from src.coach_intelligence.models.coach_explanation import (
    CoachExplanation,
)


class CoachExplanationEngine:
    """
    Fase 11.6.

    Produz explicação determinística a partir dos resultados calculados.
    Não recalcula Performance e não usa LLM para decidir estratégia.
    """

    STRATEGY_LABELS = {
        "BUILD_FOUNDATION": "Construir fundamentos",
        "CONSOLIDATE": "Consolidar execução",
        "CHALLENGE": "Aumentar o desafio",
        "CHANGE_APPROACH": "Mudar a abordagem",
        "MAINTAIN": "Manter o plano",
    }

    LEVEL_LABELS = {
        "NOT_EVALUATED": "Não avaliado",
        "BEGINNER": "Iniciante",
        "DEVELOPING": "Em desenvolvimento",
        "COMPETENT": "Competente",
        "ADVANCED": "Avançado",
        "MASTERED": "Dominado",
    }

    TREND_LABELS = {
        "INSUFFICIENT_HISTORY": "histórico insuficiente",
        "IMPROVING": "melhorando",
        "STABLE": "estável",
        "REGRESSING": "regredindo",
    }

    EFFECTIVENESS_LABELS = {
        "INSUFFICIENT_HISTORY": "histórico insuficiente",
        "PROMISING": "promissora",
        "LOW_OBSERVED_EFFECTIVENESS": "baixa efetividade observada",
        "STABLE_EFFECT": "efeito estável",
        "MIXED": "resultado misto",
    }

    ANTI_LOOP_LABELS = {
        "CONTINUE": "continuar",
        "ROTATE_TASK": "rotacionar exercício",
        "REASSESS": "reavaliar abordagem",
        "COOLDOWN_SKILL": "pausa pedagógica",
    }

    DIFFICULTY_LABELS = {
        "FOUNDATION": "Fundamentos",
        "INTERMEDIATE": "Intermediário",
        "ADVANCED": "Avançado",
    }

    NEXT_STEPS = {
        "BUILD_FOUNDATION": (
            "Mantenha o exercício simples e repetível até existir evidência "
            "suficiente para avançar."
        ),
        "CONSOLIDATE": (
            "Repita o princípio treinado com consistência antes de aumentar "
            "a dificuldade."
        ),
        "CHALLENGE": (
            "O próximo ciclo pode exigir uma decisão mais difícil dentro da "
            "mesma Skill, sem mudar a prioridade."
        ),
        "CHANGE_APPROACH": (
            "Evite repetir automaticamente a mesma abordagem; use a rotação "
            "ou reavaliação indicada pelo Learning Loop."
        ),
        "MAINTAIN": (
            "Continue o plano atual e acumule mais evidência antes de fazer "
            "uma mudança pedagógica."
        ),
    }

    @classmethod
    def explain(
        cls,
        *,
        strategy,
        foundation: dict,
    ) -> CoachExplanation:
        skill_id = strategy.priority_skill_id
        profile = foundation.get(
            "profile",
            {},
        )
        skills = (
            profile.get(
                "skills",
                {}
            )
            if isinstance(
                profile,
                dict,
            )
            else {}
        )
        skill = (
            skills.get(
                skill_id,
                {}
            )
            if isinstance(
                skills,
                dict,
            )
            else {}
        )

        skill_name = str(
            skill.get(
                "skill_name",
                skill_id.replace(
                    "_",
                    " ",
                ).title(),
            )
        )

        title = (
            f"{skill_name}: "
            f"{cls.STRATEGY_LABELS.get(strategy.strategy, strategy.strategy)}"
        )

        score_text = (
            f"score atual {strategy.current_score:.2f}"
            if strategy.current_score is not None
            else "sem score técnico direto"
        )

        level_label = cls.LEVEL_LABELS.get(
            str(strategy.current_level).upper(),
            str(strategy.current_level),
        )

        trend_label = cls.TREND_LABELS.get(
            str(strategy.training_trend).upper(),
            str(strategy.training_trend),
        )

        effectiveness_label = cls.EFFECTIVENESS_LABELS.get(
            str(strategy.task_effectiveness).upper(),
            str(strategy.task_effectiveness),
        )

        anti_loop_label = cls.ANTI_LOOP_LABELS.get(
            str(strategy.anti_loop_action).upper(),
            str(strategy.anti_loop_action),
        )

        summary = (
            f"O foco continua em {skill_name}. O perfil está em "
            f"{level_label}, com {score_text}, tendência de "
            f"{trend_label} e estratégia "
            f"{cls.STRATEGY_LABELS.get(strategy.strategy, strategy.strategy)}. "
            f"{strategy.rationale}"
        )

        evidence = [
            f"Nível atual: {level_label}.",
            (
                f"Tendência de treino: "
                f"{trend_label}."
            ),
            (
                f"Efetividade observada da task atual: "
                f"{effectiveness_label}."
            ),
            (
                f"Proteção anti-loop: "
                f"{anti_loop_label}."
            ),
        ]

        if strategy.current_difficulty:
            difficulty_label = cls.DIFFICULTY_LABELS.get(
                str(strategy.current_difficulty).upper(),
                str(strategy.current_difficulty),
            )

            evidence.append(
                "Dificuldade atual: "
                f"{difficulty_label}."
            )

        cross = cls._relevant_cross_skill(
            foundation=foundation,
            skill_id=skill_id,
        )

        limitations = [
            (
                "A estratégia descreve evidências observadas; não prova que "
                "o exercício causou melhora ou piora."
            ),
            (
                "Learning Priority continua sendo a fonte da Skill prioritária."
            ),
        ]

        if cross is not None:
            evidence.append(
                "Sinal relacionado: "
                f"{cross.get('rationale', '')}"
            )
            limitations.append(
                str(
                    cross.get(
                        "limitation",
                        "O sinal cross-skill não prova causalidade.",
                    )
                )
            )

        return CoachExplanation(
            title=title,
            summary=summary,
            next_step=cls.NEXT_STEPS.get(
                strategy.strategy,
                cls.NEXT_STEPS[
                    "MAINTAIN"
                ],
            ),
            evidence=tuple(
                evidence
            ),
            limitations=tuple(
                limitations
            ),
            source="deterministic",
        )

    @staticmethod
    def _relevant_cross_skill(
        *,
        foundation: dict,
        skill_id: str,
    ) -> dict | None:
        items = foundation.get(
            "cross_skill_insights",
            [],
        )

        if not isinstance(
            items,
            list,
        ):
            return None

        for item in items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            if skill_id in {
                item.get(
                    "source_skill_id"
                ),
                item.get(
                    "target_skill_id"
                ),
            }:
                return item

        return None
