from __future__ import annotations

from typing import Any

from src.learning.models.habit import (
    Habit,
    HabitEvidence,
)


class HabitEngine:
    """
    Detecta hábitos a partir do coach_context já calculado.

    Regras de arquitetura:
    - não acessa a Riot API;
    - não cria métricas novas;
    - não usa IA;
    - não infere intenção;
    - não afirma que o jogador "viu", "ignorou", "forçou" ou "decidiu"
      algo que o histórico não consiga observar diretamente.
    """

    MIN_MATCHES = 10

    @classmethod
    def detect(
        cls,
        *,
        coach_context: dict[str, Any],
    ) -> tuple[Habit, ...]:
        habits: list[Habit] = []

        composition = coach_context.get("composition", {}) or {}
        contest = coach_context.get("contest", {}) or {}
        economy = coach_context.get("economy", {}) or {}

        for habit in (
            cls._contest_habit(contest),
            cls._composition_habit(composition),
            cls._economy_habit(economy),
        ):
            if habit is not None:
                habits.append(habit)

        return tuple(
            sorted(
                habits,
                key=cls._habit_order,
            )
        )

    @classmethod
    def _contest_habit(
        cls,
        context: dict[str, Any],
    ) -> Habit | None:
        matches = cls._int(context.get("matches_analyzed"))

        if matches < cls.MIN_MATCHES:
            return None

        carry_rate = cls._float(context.get("carry_contest_rate"))
        high_rate = cls._float(context.get("high_contest_rate"))

        if carry_rate < 45.0:
            return None

        impact_raw = context.get("placement_impact")
        impact = (
            cls._float(impact_raw)
            if impact_raw is not None
            else None
        )

        impact_label = str(
            context.get(
                "placement_impact_label",
                "indeterminado",
            )
        ).strip().lower()

        confidence = cls._confidence(
            matches=matches,
            source_confidence=cls._float(
                context.get("confidence")
            ),
            signal_strength=carry_rate,
        )

        if impact_label in {"alto", "relevante"}:
            direction = "negative"
            status = "established"
            interpretation = (
                "O histórico mostra exposição recorrente do carry à "
                "contestação, e a interpretação determinística atual "
                "também associa esse padrão a piora de colocação. "
                "Isso descreve um padrão observado; não prova que o "
                "jogador percebeu a contestação e decidiu permanecer nela."
            )
        elif impact_label in {
            "leve",
            "neutro",
            "sem_piora_observada",
        }:
            direction = "neutral"
            status = "observed"
            interpretation = (
                "O carry aparece contestado com frequência recorrente, "
                "mas o histórico atual não sustenta tratar essa exposição "
                "como causa relevante de piora dos resultados."
            )
        else:
            direction = "neutral"
            status = "observed"
            interpretation = (
                "O carry aparece contestado com frequência recorrente. "
                "A amostra ainda não permite atribuir um efeito confiável "
                "desse padrão à colocação."
            )

        evidence = [
            HabitEvidence(
                key="carry_contest_rate",
                label="Carry contestado",
                value=round(carry_rate, 2),
                unit="%",
            ),
            HabitEvidence(
                key="high_contest_rate",
                label="Contestação alta",
                value=round(high_rate, 2),
                unit="%",
            ),
        ]

        if impact is not None:
            evidence.append(
                HabitEvidence(
                    key="placement_impact",
                    label="Impacto observado na colocação",
                    value=round(impact, 2),
                    unit="posições",
                )
            )

        return Habit(
            habit_id="recurring_carry_contest_exposure",
            category="contest",
            label="Exposição recorrente do carry à contestação",
            direction=direction,
            status=status,
            confidence=confidence,
            interpretation=interpretation,
            evidence=tuple(evidence),
            related_skill_id=None,
            related_skill_hint="lobby_reading",
        )

    @classmethod
    def _composition_habit(
        cls,
        context: dict[str, Any],
    ) -> Habit | None:
        matches = cls._int(context.get("matches_analyzed"))

        if matches < cls.MIN_MATCHES:
            return None

        diversity = cls._float(context.get("diversity_rate"))
        repetition = cls._float(context.get("repetition_rate"))
        forces = bool(context.get("forces_composition", False))
        usage_rate = cls._float(
            context.get("most_used_usage_rate")
        )

        if (
            diversity >= 70.0
            and repetition < 35.0
            and not forces
        ):
            return Habit(
                habit_id="composition_flexibility",
                category="composition",
                label="Flexibilidade recorrente entre composições",
                direction="positive",
                status="established",
                confidence=cls._confidence(
                    matches=matches,
                    signal_strength=diversity,
                ),
                interpretation=(
                    "O histórico mostra alta variedade recorrente entre "
                    "composições e não indica concentração excessiva em "
                    "uma única linha. Isso descreve flexibilidade entre "
                    "partidas, sem afirmar como as decisões aconteceram "
                    "dentro de cada jogo."
                ),
                evidence=(
                    HabitEvidence(
                        key="diversity_rate",
                        label="Diversidade de composições",
                        value=round(diversity, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="repetition_rate",
                        label="Taxa de repetição",
                        value=round(repetition, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="most_used_usage_rate",
                        label="Uso da composição mais frequente",
                        value=round(usage_rate, 2),
                        unit="%",
                    ),
                ),
                related_skill_id=None,
                related_skill_hint="composition_flexibility",
            )

        if (
            diversity >= 50.0
            and repetition < 35.0
            and not forces
        ):
            return Habit(
                habit_id="composition_variety",
                category="composition",
                label="Variedade recorrente entre composições",
                direction="positive",
                status="observed",
                confidence=cls._confidence(
                    matches=matches,
                    signal_strength=diversity,
                ),
                interpretation=(
                    "O histórico mostra variedade recorrente entre "
                    "composições e baixa repetição, mas o sinal ainda não "
                    "atingiu o nível definido para tratar a flexibilidade "
                    "como um padrão estabelecido."
                ),
                evidence=(
                    HabitEvidence(
                        key="diversity_rate",
                        label="Diversidade de composições",
                        value=round(diversity, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="repetition_rate",
                        label="Taxa de repetição",
                        value=round(repetition, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="most_used_usage_rate",
                        label="Uso da composição mais frequente",
                        value=round(usage_rate, 2),
                        unit="%",
                    ),
                ),
                related_skill_id=None,
                related_skill_hint="composition_flexibility",
            )

        if (
            forces
            or repetition >= 35.0
            or usage_rate >= 40.0
        ):
            return Habit(
                habit_id="composition_concentration",
                category="composition",
                label="Concentração recorrente em poucas linhas",
                direction="negative",
                status=(
                    "established"
                    if forces or repetition >= 50.0
                    else "observed"
                ),
                confidence=cls._confidence(
                    matches=matches,
                    signal_strength=max(
                        repetition,
                        usage_rate,
                    ),
                ),
                interpretation=(
                    "O histórico mostra concentração recorrente em poucas "
                    "linhas de composição. Isso não significa, por si só, "
                    "que o jogador esteja deliberadamente forçando uma "
                    "composição em todas as partidas."
                ),
                evidence=(
                    HabitEvidence(
                        key="diversity_rate",
                        label="Diversidade de composições",
                        value=round(diversity, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="repetition_rate",
                        label="Taxa de repetição",
                        value=round(repetition, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="most_used_usage_rate",
                        label="Uso da composição mais frequente",
                        value=round(usage_rate, 2),
                        unit="%",
                    ),
                ),
                related_skill_id=None,
                related_skill_hint="composition_flexibility",
            )

        return None

    @classmethod
    def _economy_habit(
        cls,
        context: dict[str, Any],
    ) -> Habit | None:
        matches = cls._int(context.get("matches_analyzed"))

        if matches < cls.MIN_MATCHES:
            return None

        label = str(
            context.get("label", "")
        ).strip().lower()

        level8 = cls._float(context.get("level_8_rate"))
        level9 = cls._float(context.get("level_9_rate"))
        gold = cls._float(context.get("average_gold_left"))
        low_level_late = cls._float(
            context.get("low_level_late_rate")
        )
        source_confidence = cls._float(
            context.get("confidence")
        )

        if (
            label in {"forte", "muito forte"}
            or (
                level8 >= 80.0
                and low_level_late <= 10.0
            )
        ):
            return Habit(
                habit_id="consistent_level_progression",
                category="economy",
                label="Progressão de nível recorrente e consistente",
                direction="positive",
                status="established",
                confidence=cls._confidence(
                    matches=matches,
                    source_confidence=source_confidence,
                    signal_strength=level8,
                ),
                interpretation=(
                    "O histórico mostra progressão consistente para níveis "
                    "altos. Esse hábito descreve o resultado recorrente da "
                    "progressão; não reconstrói o momento exato em que o "
                    "jogador gastou ouro ou comprou experiência."
                ),
                evidence=(
                    HabitEvidence(
                        key="level_8_rate",
                        label="Chegou ao nível 8",
                        value=round(level8, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="level_9_rate",
                        label="Chegou ao nível 9",
                        value=round(level9, 2),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="low_level_late_rate",
                        label="Partidas longas em nível baixo",
                        value=round(
                            low_level_late,
                            2,
                        ),
                        unit="%",
                    ),
                ),
                related_skill_id="leveling",
                related_skill_hint="economy_progression",
            )

        if (
            gold >= 25.0
            and level9 < 30.0
        ):
            return Habit(
                habit_id="resources_remaining_at_end",
                category="economy",
                label="Recursos finais recorrentes sem progressão máxima",
                direction="negative",
                status="observed",
                confidence=cls._confidence(
                    matches=matches,
                    source_confidence=source_confidence,
                    signal_strength=min(
                        100.0,
                        gold * 2.0,
                    ),
                ),
                interpretation=(
                    "O histórico combina ouro restante elevado com baixa "
                    "frequência de nível 9. Isso sugere um padrão de recursos "
                    "finais disponíveis, mas não permite afirmar quando ou "
                    "como esses recursos deveriam ter sido gastos."
                ),
                evidence=(
                    HabitEvidence(
                        key="average_gold_left",
                        label="Ouro restante médio",
                        value=round(gold, 2),
                    ),
                    HabitEvidence(
                        key="level_9_rate",
                        label="Chegou ao nível 9",
                        value=round(level9, 2),
                        unit="%",
                    ),
                ),
                related_skill_id="economy",
                related_skill_hint="resource_conversion",
            )

        if low_level_late >= 25.0:
            return Habit(
                habit_id="late_low_level_pattern",
                category="economy",
                label="Progressão tardia frequentemente limitada",
                direction="negative",
                status="observed",
                confidence=cls._confidence(
                    matches=matches,
                    source_confidence=source_confidence,
                    signal_strength=low_level_late,
                ),
                interpretation=(
                    "Partidas longas terminam em nível baixo com frequência "
                    "recorrente. O padrão é observável, mas não revela o "
                    "timing das decisões econômicas que produziram esse "
                    "resultado."
                ),
                evidence=(
                    HabitEvidence(
                        key="low_level_late_rate",
                        label="Partidas longas em nível baixo",
                        value=round(
                            low_level_late,
                            2,
                        ),
                        unit="%",
                    ),
                    HabitEvidence(
                        key="level_8_rate",
                        label="Chegou ao nível 8",
                        value=round(level8, 2),
                        unit="%",
                    ),
                ),
                related_skill_id="leveling",
                related_skill_hint="economy_progression",
            )

        return None

    @classmethod
    def diagnose(
        cls,
        *,
        coach_context: dict[str, Any],
    ) -> tuple["HabitDiagnostic", ...]:
        """
        Explica por que um Habit foi ou não declarado.

        Esta função não altera thresholds nem regras de detecção.
        Serve apenas para transparência, testes e inspeção.
        """
        from src.learning.models.habit import HabitDiagnostic

        diagnostics = (
            cls._diagnose_contest(
                coach_context.get(
                    "contest",
                    {},
                ) or {}
            ),
            cls._diagnose_composition(
                coach_context.get(
                    "composition",
                    {},
                ) or {}
            ),
            cls._diagnose_economy(
                coach_context.get(
                    "economy",
                    {},
                ) or {}
            ),
        )

        return diagnostics

    @classmethod
    def _diagnose_contest(
        cls,
        context: dict[str, Any],
    ) -> "HabitDiagnostic":
        from src.learning.models.habit import HabitDiagnostic

        matches = cls._int(
            context.get(
                "matches_analyzed"
            )
        )
        carry_rate = cls._float(
            context.get(
                "carry_contest_rate"
            )
        )
        impact_label = str(
            context.get(
                "placement_impact_label",
                "indeterminado",
            )
        ).strip().lower()

        checks = (
            f"Partidas analisadas: {matches} (mínimo {cls.MIN_MATCHES})",
            f"Carry contestado: {carry_rate:.2f}% (mínimo 45.00%)",
            f"Classificação do impacto: {impact_label}",
        )

        if matches < cls.MIN_MATCHES:
            return HabitDiagnostic(
                category="contest",
                declared_habit_id=None,
                status="not_declared",
                explanation=(
                    "Amostra abaixo do mínimo necessário para declarar "
                    "um hábito de contestação."
                ),
                checks=checks,
            )

        if carry_rate < 45.0:
            return HabitDiagnostic(
                category="contest",
                declared_habit_id=None,
                status="not_declared",
                explanation=(
                    "A exposição do carry à contestação não atingiu o "
                    "threshold mínimo de recorrência."
                ),
                checks=checks,
            )

        return HabitDiagnostic(
            category="contest",
            declared_habit_id="recurring_carry_contest_exposure",
            status="declared",
            explanation=(
                "A exposição do carry à contestação atingiu o threshold "
                "de recorrência. A direção do Habit depende da interpretação "
                "determinística do impacto na colocação."
            ),
            checks=checks,
        )

    @classmethod
    def _diagnose_composition(
        cls,
        context: dict[str, Any],
    ) -> "HabitDiagnostic":
        from src.learning.models.habit import HabitDiagnostic

        matches = cls._int(
            context.get(
                "matches_analyzed"
            )
        )
        diversity = cls._float(
            context.get(
                "diversity_rate"
            )
        )
        repetition = cls._float(
            context.get(
                "repetition_rate"
            )
        )
        forces = bool(
            context.get(
                "forces_composition",
                False,
            )
        )
        usage_rate = cls._float(
            context.get(
                "most_used_usage_rate"
            )
        )

        checks = (
            f"Partidas analisadas: {matches} (mínimo {cls.MIN_MATCHES})",
            f"Diversidade: {diversity:.2f}% "
            "(variedade >= 50.00% | flexibilidade estabelecida >= 70.00%)",
            f"Repetição: {repetition:.2f}% (flexibilidade < 35.00%)",
            f"Força composição: {'Sim' if forces else 'Não'}",
            f"Uso da composição mais frequente: {usage_rate:.2f}% "
            "(concentração >= 40.00%)",
        )

        if matches < cls.MIN_MATCHES:
            return HabitDiagnostic(
                category="composition",
                declared_habit_id=None,
                status="not_declared",
                explanation=(
                    "Amostra abaixo do mínimo necessário para declarar "
                    "um hábito de composição."
                ),
                checks=checks,
            )

        if (
            diversity >= 70.0
            and repetition < 35.0
            and not forces
        ):
            return HabitDiagnostic(
                category="composition",
                declared_habit_id="composition_flexibility",
                status="declared",
                explanation=(
                    "A combinação de alta diversidade, baixa repetição "
                    "e ausência de concentração sustenta flexibilidade "
                    "recorrente como padrão estabelecido."
                ),
                checks=checks,
            )

        if (
            diversity >= 50.0
            and repetition < 35.0
            and not forces
        ):
            return HabitDiagnostic(
                category="composition",
                declared_habit_id="composition_variety",
                status="declared",
                explanation=(
                    "A diversidade e a baixa repetição sustentam variedade "
                    "recorrente, mas o sinal ainda não atingiu o threshold "
                    "de flexibilidade estabelecida."
                ),
                checks=checks,
            )

        if (
            forces
            or repetition >= 35.0
            or usage_rate >= 40.0
        ):
            return HabitDiagnostic(
                category="composition",
                declared_habit_id="composition_concentration",
                status="declared",
                explanation=(
                    "A concentração recorrente foi declarada porque pelo "
                    "menos um dos sinais de concentração atingiu o threshold."
                ),
                checks=checks,
            )

        return HabitDiagnostic(
            category="composition",
            declared_habit_id=None,
            status="not_declared",
            explanation=(
                "Os dados não atingiram os critérios de variedade "
                "recorrente nem os critérios de concentração recorrente. "
                "O TFT Insight prefere não declarar um Habit nesse caso."
            ),
            checks=checks,
        )

    @classmethod
    def _diagnose_economy(
        cls,
        context: dict[str, Any],
    ) -> "HabitDiagnostic":
        from src.learning.models.habit import HabitDiagnostic

        matches = cls._int(
            context.get(
                "matches_analyzed"
            )
        )
        label = str(
            context.get(
                "label",
                "",
            )
        ).strip().lower()
        level8 = cls._float(
            context.get(
                "level_8_rate"
            )
        )
        level9 = cls._float(
            context.get(
                "level_9_rate"
            )
        )
        gold = cls._float(
            context.get(
                "average_gold_left"
            )
        )
        low_level_late = cls._float(
            context.get(
                "low_level_late_rate"
            )
        )

        checks = (
            f"Partidas analisadas: {matches} (mínimo {cls.MIN_MATCHES})",
            f"Classificação econômica: {label or '-'}",
            f"Nível 8: {level8:.2f}% (consistência >= 80.00%)",
            f"Nível 9: {level9:.2f}% (recursos finais < 30.00%)",
            f"Ouro restante médio: {gold:.2f} (recursos finais >= 25.00)",
            f"Partidas longas em nível baixo: {low_level_late:.2f}% "
            "(limitação tardia >= 25.00%)",
        )

        if matches < cls.MIN_MATCHES:
            return HabitDiagnostic(
                category="economy",
                declared_habit_id=None,
                status="not_declared",
                explanation=(
                    "Amostra abaixo do mínimo necessário para declarar "
                    "um hábito de economia/progressão."
                ),
                checks=checks,
            )

        if (
            label in {
                "forte",
                "muito forte",
            }
            or (
                level8 >= 80.0
                and low_level_late <= 10.0
            )
        ):
            return HabitDiagnostic(
                category="economy",
                declared_habit_id="consistent_level_progression",
                status="declared",
                explanation=(
                    "A progressão consistente foi declarada porque a "
                    "classificação econômica ou os indicadores de nível "
                    "atingiram os critérios atuais."
                ),
                checks=checks,
            )

        if (
            gold >= 25.0
            and level9 < 30.0
        ):
            return HabitDiagnostic(
                category="economy",
                declared_habit_id="resources_remaining_at_end",
                status="declared",
                explanation=(
                    "O histórico combina ouro restante elevado com baixa "
                    "frequência de nível 9."
                ),
                checks=checks,
            )

        if low_level_late >= 25.0:
            return HabitDiagnostic(
                category="economy",
                declared_habit_id="late_low_level_pattern",
                status="declared",
                explanation=(
                    "Partidas longas terminam em nível baixo com frequência "
                    "suficiente para declarar o padrão."
                ),
                checks=checks,
            )

        return HabitDiagnostic(
            category="economy",
            declared_habit_id=None,
            status="not_declared",
            explanation=(
                "Nenhum padrão econômico/progressão atingiu os thresholds "
                "atuais para declaração de Habit."
            ),
            checks=checks,
        )


    @staticmethod
    def _habit_order(
        habit: Habit,
    ) -> tuple[int, float]:
        direction_order = {
            "negative": 0,
            "neutral": 1,
            "positive": 2,
        }

        return (
            direction_order.get(
                habit.direction,
                9,
            ),
            -habit.confidence,
        )

    @staticmethod
    def _float(
        value: Any,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _int(
        value: Any,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _confidence(
        cls,
        *,
        matches: int,
        source_confidence: float = 0.0,
        signal_strength: float = 0.0,
    ) -> float:
        sample_component = min(
            max(matches, 0),
            30,
        ) / 30.0 * 35.0

        source_component = min(
            max(source_confidence, 0.0),
            100.0,
        ) * 0.35

        signal_component = min(
            max(signal_strength, 0.0),
            100.0,
        ) * 0.30

        return round(
            min(
                100.0,
                max(
                    0.0,
                    sample_component
                    + source_component
                    + signal_component,
                ),
            ),
            2,
        )
