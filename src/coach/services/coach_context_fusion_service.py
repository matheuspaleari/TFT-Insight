"""
Coach Context Fusion V1.

Combina contexto competitivo, prioridade oficial, plano de treino e sinais
estratégicos já calculados para explicar a decisão do Coach.

Esta camada NÃO escolhe Skill, NÃO reordena Learning Priority e NÃO altera
missão/dificuldade. Ela apenas organiza a decisão já tomada em linguagem de
produto:

- problema observado;
- foco de treino;
- ponto forte a preservar;
- contexto competitivo;
- sinais de apoio.

Termo público:
"contestação". A chave interna "contest" continua preservada nos contratos
legados para evitar quebra de compatibilidade.
"""

from __future__ import annotations

from typing import Any


class CoachContextFusionService:
    @classmethod
    def build(
        cls,
        *,
        priority_plan,
        training_plan,
        mission,
        competitive_spectrum: dict[str, Any] | None,
        coach_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        spectrum = (
            competitive_spectrum
            if isinstance(competitive_spectrum, dict)
            else {}
        )
        strategic = (
            coach_context
            if isinstance(coach_context, dict)
            else {}
        )

        primary = getattr(
            priority_plan,
            "primary",
            None,
        )

        problem = cls._problem_observed(
            primary=primary,
            training_plan=training_plan,
            mission=mission,
        )

        focus = cls._training_focus(
            primary=primary,
            training_plan=training_plan,
            mission=mission,
        )

        strength = cls._strength_to_preserve(
            priority_plan=priority_plan,
            spectrum=spectrum,
        )

        competitive = cls._competitive_context(
            spectrum=spectrum,
        )

        supporting = cls._supporting_signals(
            coach_context=strategic,
        )

        return {
            "problem_observed": problem,
            "training_focus": focus,
            "strength_to_preserve": strength,
            "competitive_context": competitive,
            "supporting_signals": supporting,
            "protections": {
                "changes_learning_priority": False,
                "changes_mission": False,
                "changes_difficulty": False,
                "predicts_rank_up": False,
            },
        }

    @staticmethod
    def _problem_observed(
        *,
        primary,
        training_plan,
        mission,
    ) -> dict[str, Any]:
        if primary is not None:
            return {
                "skill_id": getattr(
                    primary,
                    "skill_id",
                    None,
                ),
                "skill_label": getattr(
                    primary,
                    "skill_label",
                    None,
                ),
                "title": (
                    f"{getattr(primary, 'skill_label', 'Foco atual')} "
                    "é a principal oportunidade de treino"
                ),
                "description": getattr(
                    primary,
                    "reason",
                    "",
                ),
                "confidence": getattr(
                    primary,
                    "confidence",
                    None,
                ),
                "source": "learning_priority",
            }

        if training_plan is not None:
            label = getattr(
                training_plan,
                "primary_skill_label",
                "Foco atual",
            )
            return {
                "skill_id": getattr(
                    training_plan,
                    "primary_skill_id",
                    None,
                ),
                "skill_label": label,
                "title": f"{label} é o foco atual",
                "description": getattr(
                    training_plan,
                    "objective",
                    "",
                ),
                "confidence": None,
                "source": "training_plan",
            }

        return {
            "skill_id": getattr(
                mission,
                "skill_id",
                None,
            ),
            "skill_label": getattr(
                mission,
                "skill_id",
                "Treino atual",
            ),
            "title": "Existe um treino ativo",
            "description": (
                "O ciclo atual continua válido até que haja evidência "
                "suficiente para uma nova decisão."
            ),
            "confidence": None,
            "source": "mission",
        }

    @staticmethod
    def _training_focus(
        *,
        primary,
        training_plan,
        mission,
    ) -> dict[str, Any]:
        objective = (
            getattr(
                training_plan,
                "objective",
                "",
            )
            if training_plan is not None
            else ""
        )

        focus_text = (
            getattr(
                primary,
                "training_focus",
                "",
            )
            if primary is not None
            else ""
        )

        return {
            "mission_title": getattr(
                mission,
                "title",
                "Missão atual",
            ),
            "games_target": getattr(
                mission,
                "games_target",
                None,
            ),
            "games_completed": getattr(
                mission,
                "games_completed",
                None,
            ),
            "remaining_games": getattr(
                mission,
                "remaining_games",
                None,
            ),
            "objective": objective,
            "training_focus": focus_text,
            "next_action": getattr(
                getattr(mission, "task", None),
                "habit",
                "",
            ),
        }

    @staticmethod
    def _strength_to_preserve(
        *,
        priority_plan,
        spectrum: dict[str, Any],
    ) -> dict[str, Any] | None:
        strengths = tuple(
            getattr(
                priority_plan,
                "strengths",
                (),
            )
            or ()
        )

        if strengths:
            item = strengths[0]
            return {
                "skill_id": getattr(
                    item,
                    "skill_id",
                    None,
                ),
                "skill_label": getattr(
                    item,
                    "skill_label",
                    "Ponto forte",
                ),
                "description": getattr(
                    item,
                    "reason",
                    "Preserve este padrão enquanto trabalha o foco principal.",
                ),
                "source": "learning_priority",
            }

        spectrum_strengths = spectrum.get(
            "strengths",
            [],
        )

        if isinstance(
            spectrum_strengths,
            list,
        ) and spectrum_strengths:
            metric = str(
                spectrum_strengths[0]
            )
            return {
                "skill_id": None,
                "skill_label": public_metric_label(
                    metric
                ),
                "description": (
                    "Este fundamento aparece como ponto forte no perfil "
                    "comparativo recente. Preserve-o enquanto trabalha "
                    "a prioridade atual."
                ),
                "source": "competitive_spectrum",
            }

        return None

    @staticmethod
    def _competitive_context(
        *,
        spectrum: dict[str, Any],
    ) -> dict[str, Any]:
        if not spectrum:
            return {
                "available": False,
                "message": (
                    "O contexto competitivo não está disponível "
                    "para esta leitura."
                ),
            }

        available = bool(
            spectrum.get("available")
        )

        if not available:
            return {
                "available": False,
                "group_label": spectrum.get(
                    "group_label"
                ),
                "current_rank": spectrum.get(
                    "current_rank"
                ),
                "message": spectrum.get(
                    "limitation"
                )
                or (
                    "Ainda não há dados suficientes para posicionar "
                    "o jogador dentro do grupo competitivo."
                ),
            }

        band = str(
            spectrum.get(
                "spectrum_band",
                "posição atual",
            )
        )
        group = str(
            spectrum.get(
                "group_label",
                "grupo competitivo",
            )
        )
        rank = str(
            spectrum.get(
                "current_rank",
                "",
            )
        )

        return {
            "available": True,
            "group_label": group,
            "current_rank": rank,
            "spectrum_band": band,
            "spectrum_percentile": spectrum.get(
                "spectrum_percentile"
            ),
            "population_size": spectrum.get(
                "population_size",
                0,
            ),
            "message": (
                f"{rank} está na faixa {band.lower()} do grupo "
                f"competitivo {group}. Essa posição contextualiza o "
                "treino, mas não decide a prioridade."
            ),
        }

    @classmethod
    def _supporting_signals(
        cls,
        *,
        coach_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        contestation = coach_context.get(
            "contest",
            {},
        ) or {}

        if isinstance(
            contestation,
            dict,
        ):
            action = cls._first_text(
                contestation,
                "action",
                "recommendation",
            )
            explanation = cls._first_text(
                contestation,
                "explanation",
                "impact_explanation",
            )

            if action or explanation:
                signals.append(
                    {
                        "id": "contestation",
                        "label": "Contestação",
                        "action": public_text(
                            action
                        ),
                        "explanation": public_text(
                            explanation
                        ),
                    }
                )

        economy = coach_context.get(
            "economy",
            {},
        ) or {}

        if isinstance(economy, dict):
            action = cls._first_text(
                economy,
                "action",
                "recommendation",
            )
            explanation = cls._first_text(
                economy,
                "explanation",
                "interpretation",
            )

            if action or explanation:
                signals.append(
                    {
                        "id": "economy",
                        "label": "Economia",
                        "action": public_text(
                            action
                        ),
                        "explanation": public_text(
                            explanation
                        ),
                    }
                )

        composition = coach_context.get(
            "composition",
            {},
        ) or {}

        if isinstance(
            composition,
            dict,
        ):
            explanation = cls._first_text(
                composition,
                "recommendation_explanation",
                "interpretation",
            )

            if explanation:
                signals.append(
                    {
                        "id": "composition",
                        "label": "Composição",
                        "action": "",
                        "explanation": public_text(
                            explanation
                        ),
                    }
                )

        return signals[:3]

    @staticmethod
    def _first_text(
        payload: dict[str, Any],
        *keys: str,
    ) -> str:
        for key in keys:
            value = payload.get(key)
            if isinstance(
                value,
                str,
            ) and value.strip():
                return value.strip()
        return ""


def public_metric_label(
    metric: str,
) -> str:
    mapping = {
        "average_damage_to_players": "Dano aos jogadores",
        "average_players_eliminated": "Eliminações por partida",
        "average_level": "Nível médio",
        "placement_standard_deviation": "Consistência",
        "top4_rate": "Taxa de Top 4",
        "win_rate": "Taxa de vitória",
        "average_gold_left": "Ouro restante",
        "bottom4_rate": "Taxa de Bottom 4",
        "average_placement": "Colocação média",
    }

    return mapping.get(
        metric,
        metric.replace(
            "_",
            " ",
        ).strip().capitalize(),
    )


def public_text(
    value: str,
) -> str:
    """
    Traduz apenas termos internos conhecidos. Não altera chaves nem contratos.
    """
    text = str(
        value or ""
    )

    replacements = (
        ("Contest score", "Índice de contestação"),
        ("contest score", "índice de contestação"),
        ("Contestação score", "Índice de contestação"),
        ("contestação score", "índice de contestação"),
        ("Contest", "Contestação"),
        ("contest", "contestação"),
    )

    for old, new in replacements:
        text = text.replace(
            old,
            new,
        )

    return text
