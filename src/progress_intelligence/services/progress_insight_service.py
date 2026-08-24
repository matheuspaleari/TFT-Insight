from __future__ import annotations

from ..models.progress_insight import ProgressInsight


class ProgressInsightService:
    LEVEL_LABELS = {
        "NOT_EVALUATED": "não avaliado",
        "BEGINNER": "iniciante",
        "DEVELOPING": "em desenvolvimento",
        "COMPETENT": "competente",
        "ADVANCED": "avançado",
        "MASTERED": "dominado",
    }

    @classmethod
    def build(
        cls,
        *,
        timelines: dict,
        development_summary,
    ) -> list[ProgressInsight]:
        insights = []

        primary = development_summary.primary_skill_id
        if primary and primary in timelines:
            points = timelines[primary]

            if len(points) >= 2:
                first = points[0]
                latest = points[-1]

                if (
                    first.score is not None
                    and latest.score is not None
                ):
                    delta = latest.score - first.score

                    if delta >= 5:
                        insights.append(
                            ProgressInsight(
                                role="progress",
                                title=f"{primary}: avanço acumulado",
                                message=(
                                    f"O score de {primary} avançou "
                                    f"{delta:+.2f} pontos desde o primeiro "
                                    "snapshot registrado."
                                ),
                                skill_id=primary,
                                evidence={
                                    "first_score": first.score,
                                    "latest_score": latest.score,
                                    "delta": delta,
                                },
                            )
                        )
                    elif delta <= -5:
                        insights.append(
                            ProgressInsight(
                                role="attention",
                                title=f"{primary}: queda acumulada",
                                message=(
                                    f"O score de {primary} caiu "
                                    f"{abs(delta):.2f} pontos desde o primeiro "
                                    "snapshot. Vale observar se o padrão "
                                    "continua nos próximos registros."
                                ),
                                skill_id=primary,
                                evidence={
                                    "first_score": first.score,
                                    "latest_score": latest.score,
                                    "delta": delta,
                                },
                            )
                        )
                    else:
                        insights.append(
                            ProgressInsight(
                                role="stable",
                                title=f"{primary}: pouca variação",
                                message=(
                                    f"O score de {primary} variou apenas "
                                    f"{delta:+.2f} pontos desde o primeiro "
                                    "snapshot; ainda não há mudança técnica "
                                    "ampla no período."
                                ),
                                skill_id=primary,
                                evidence={
                                    "first_score": first.score,
                                    "latest_score": latest.score,
                                    "delta": delta,
                                },
                            )
                        )

                if first.level != latest.level:
                    insights.append(
                        ProgressInsight(
                            role="milestone",
                            title=f"{primary}: mudança de nível",
                            message=(
                                f"O nível observado mudou de "
                                f"{cls.LEVEL_LABELS.get(first.level, first.level)} "
                                f"para {cls.LEVEL_LABELS.get(latest.level, latest.level)}."
                            ),
                            skill_id=primary,
                            evidence={
                                "first_level": first.level,
                                "latest_level": latest.level,
                            },
                        )
                    )
            else:
                insights.append(
                    ProgressInsight(
                        role="insufficient",
                        title=f"{primary}: histórico em construção",
                        message=(
                            "Ainda existe apenas um snapshot longitudinal "
                            "dessa Skill. O TFT Insight precisa de mais "
                            "registros antes de afirmar evolução de longo prazo."
                        ),
                        skill_id=primary,
                        evidence={
                            "snapshots": len(points),
                        },
                    )
                )

        if development_summary.status == "NEEDS_ATTENTION":
            insights.append(
                ProgressInsight(
                    role="attention",
                    title="Desenvolvimento geral pede atenção",
                    message=(
                        "Há pelo menos uma Skill com tendência regressiva. "
                        "A leitura é observacional e não altera a prioridade "
                        "de treinamento automaticamente."
                    ),
                    skill_id=None,
                    evidence={
                        "regressing_skills": list(
                            development_summary.regressing_skills
                        )
                    },
                )
            )

        if not insights:
            insights.append(
                ProgressInsight(
                    role="insufficient",
                    title="Histórico longitudinal insuficiente",
                    message=(
                        "Ainda não há snapshots suficientes para construir "
                        "uma leitura de progresso de longo prazo."
                    ),
                    skill_id=None,
                    evidence={},
                )
            )

        return insights
