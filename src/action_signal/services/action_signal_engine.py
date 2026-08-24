from __future__ import annotations

from src.action_signal.models.action_signal import (
    ActionSignal,
    ActionSignalEvidence,
    ActionSignalReport,
    ActionSignalStrength,
)


class ActionSignalEngine:
    """
    Action Signal Engine V1.

    Converte sinais já calculados em ações seguras para a próxima partida.

    Regras:
    - não inventa timing/eventos ausentes da telemetria;
    - não troca Learning Priority;
    - não troca missão;
    - não transforma correlação em causalidade;
    - prioriza a Skill atual;
    - entrega no máximo 1 PRIMARY + 2 SECONDARY + 2 WATCH.
    """

    @classmethod
    def build(
        cls,
        *,
        post_match_report,
        post_match_analysis,
        historical_context,
        active_skill_id: str | None,
        active_skill_label: str | None,
        mission_title: str | None,
    ) -> ActionSignalReport:
        signals: list[ActionSignal] = []

        skill_id = (active_skill_id or "").lower()
        skill_label = active_skill_label or active_skill_id or "foco atual"
        mission = mission_title or "missão atual"

        historical = {
            item.metric_id: item
            for item in historical_context.metrics
        }

        # 1) Skill atual ganha prioridade.
        if skill_id == "leveling":
            level = historical.get("level")
            if level is not None:
                signal_value = getattr(level.signal, "value", str(level.signal))

                if signal_value == "WORSENING":
                    signals.append(
                        ActionSignal(
                            signal_id="leveling_plan_before_xp",
                            title="Planeje a próxima subida antes de gastar",
                            action=(
                                "Antes de comprar experiência, defina qual nível você quer "
                                "alcançar e qual condição faria você estabilizar antes."
                            ),
                            reason=(
                                "Seu nível final médio vem terminando mais baixo no bloco recente. "
                                "Isso não prova piora de decisão, então a ação proposta é de planejamento, "
                                "não de correção automática."
                            ),
                            strength=ActionSignalStrength.PRIMARY,
                            evidence=ActionSignalEvidence.HISTORICAL,
                            skill_id="leveling",
                            metric_id="level",
                            confidence=0.78,
                        )
                    )
                else:
                    signals.append(
                        ActionSignal(
                            signal_id="leveling_keep_plan",
                            title="Mantenha um plano claro de nível",
                            action=(
                                "Continue definindo previamente seu próximo momento de subida "
                                "e reavalie se o board pedir estabilização."
                            ),
                            reason=(
                                "O histórico de nível final não mostra uma queda forte o bastante "
                                "para justificar uma abordagem mais agressiva."
                            ),
                            strength=ActionSignalStrength.PRIMARY,
                            evidence=ActionSignalEvidence.HISTORICAL,
                            skill_id="leveling",
                            metric_id="level",
                            confidence=0.68,
                        )
                    )

        # 2) Contextos da última partida viram sinais secundários.
        for section in getattr(post_match_report, "supporting_sections", ()):
            sid = getattr(section, "section_id", "")
            text = getattr(section, "text", "")

            if "pressure" in sid or "damage" in sid:
                signals.append(
                    ActionSignal(
                        signal_id="board_pressure_check",
                        title="Cheque se seu board está pressionando o lobby",
                        action=(
                            "Antes de investir pesado em nível ou economia, compare se seu board "
                            "está preservando vida e conseguindo converter força em pressão."
                        ),
                        reason=text or (
                            "A pressão da última partida ficou abaixo do padrão recente."
                        ),
                        strength=ActionSignalStrength.SECONDARY,
                        evidence=ActionSignalEvidence.OBSERVED,
                        metric_id="total_damage_to_players",
                        confidence=0.72,
                    )
                )

            elif "placement" in sid:
                signals.append(
                    ActionSignal(
                        signal_id="result_is_context",
                        title="Não reaja demais ao resultado isolado",
                        action=(
                            "Use a colocação como contexto, mas evite mudar toda a abordagem "
                            "por causa de uma única partida."
                        ),
                        reason=text or (
                            "A colocação da partida foi abaixo do padrão recente."
                        ),
                        strength=ActionSignalStrength.WATCH,
                        evidence=ActionSignalEvidence.OBSERVED,
                        metric_id="placement",
                        confidence=0.64,
                    )
                )

        # 3) Histórico recorrente adiciona watch signals.
        for metric in historical_context.metrics:
            signal_value = getattr(metric.signal, "value", str(metric.signal))

            if signal_value in ("RECURRING_LOW", "WORSENING"):
                if metric.metric_id == "total_damage_to_players":
                    signals.append(
                        ActionSignal(
                            signal_id="historical_pressure_watch",
                            title="Acompanhe a pressão nas próximas partidas",
                            action=(
                                "Observe se o board continua causando pouco impacto antes "
                                "de assumir que o problema vem de Leveling."
                            ),
                            reason=(
                                "O histórico mostra um sinal recorrente ou em queda na pressão."
                            ),
                            strength=ActionSignalStrength.WATCH,
                            evidence=ActionSignalEvidence.HISTORICAL,
                            metric_id=metric.metric_id,
                            confidence=0.67,
                        )
                    )

        primary = next(
            (
                item
                for item in signals
                if item.strength == ActionSignalStrength.PRIMARY
            ),
            None,
        )

        secondary = tuple(
            item
            for item in signals
            if item.strength == ActionSignalStrength.SECONDARY
        )[:2]

        watch = tuple(
            item
            for item in signals
            if item.strength == ActionSignalStrength.WATCH
        )[:2]

        if primary is None:
            primary = ActionSignal(
                signal_id="keep_mission",
                title=f"Continue o foco em {skill_label}",
                action=(
                    f"Leve a missão “{mission}” para a próxima partida e observe "
                    "se o mesmo padrão se repete."
                ),
                reason=(
                    "Os sinais atuais não justificam trocar a prioridade de treino."
                ),
                strength=ActionSignalStrength.PRIMARY,
                evidence=ActionSignalEvidence.COMBINED,
                skill_id=skill_id or None,
                confidence=0.55,
            )

        summary = (
            f"Prioridade: {primary.title}. "
            f"{len(secondary)} apoio(s) e {len(watch)} sinal(is) para acompanhar."
        )

        return ActionSignalReport(
            primary=primary,
            secondary=secondary,
            watch=watch,
            summary=summary,
            changes_learning_priority=False,
            changes_mission=False,
            changes_difficulty=False,
            changes_evidence_class=False,
            counts_as_mission_evidence=False,
            predicts_rank_up=False,
        )
