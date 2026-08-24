from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class AdaptiveCoachReport:
    headline: str
    summary: str
    personalized_actions: tuple[str, ...] = field(
        default_factory=tuple
    )
    comparisons: tuple = field(default_factory=tuple)
    caveats: tuple[str, ...] = field(default_factory=tuple)


class AdaptiveCoachEngine:
    @classmethod
    def analyze(
        cls,
        *,
        recommendation_suite,
        comparisons: tuple,
    ) -> AdaptiveCoachReport:
        actions = []

        primary = recommendation_suite.priorities.primary_priority

        if primary is not None:
            actions.append(
                f"Prioridade pessoal: {primary.action}"
            )

        action_by_metric = {
            "top4_rate": (
                "Aumente a consistência de Top 4 antes "
                "de buscar mais vitórias."
            ),
            "win_rate": (
                "Revise como converter Top 4 em Top 1."
            ),
            "average_placement": (
                "Priorize linhas de menor risco para "
                "reduzir a colocação média."
            ),
            "average_level": (
                "Revise o timing de nível e estabilização."
            ),
            "level_8_rate": (
                "Proteja economia para chegar ao nível 8."
            ),
            "level_9_rate": (
                "Identifique partidas em que vale buscar nível 9."
            ),
            "average_damage": (
                "Fortaleça o tabuleiro intermediário "
                "para gerar mais pressão."
            ),
        }

        below = [
            item
            for item in comparisons
            if item.label == "Abaixo do Challenger"
        ]

        for item in sorted(
            below,
            key=lambda value: value.percentile_estimate,
        )[:3]:
            actions.append(
                action_by_metric.get(
                    item.metric,
                    f"Melhore {item.metric}.",
                )
            )

        if not actions:
            actions.append(
                "Mantenha o padrão e aumente a amostra."
            )

        return AdaptiveCoachReport(
            headline="Plano adaptativo de melhoria",
            summary=(
                "O plano combina histórico pessoal, "
                "prioridades e benchmark Challenger."
            ),
            personalized_actions=tuple(actions[:5]),
            comparisons=comparisons,
            caveats=(
                (
                    "Use benchmark do mesmo patch e set."
                ),
                (
                    "Percentis são estimativas sem distribuição completa."
                ),
            ),
        )
