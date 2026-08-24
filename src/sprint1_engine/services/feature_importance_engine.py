from src.sprint1_engine.models import (
    FeatureContribution,
    FeatureImportanceReport,
)


class FeatureImportanceEngine:
    """Explica a previsão por contribuições determinísticas e auditáveis."""

    WEIGHTS = {
        "historical_top4": 0.35,
        "challenger_top4": 0.15,
        "strategic": 0.25,
        "contest": 0.15,
        "flex": 0.10,
    }

    LABELS = {
        "historical_top4": "Histórico pessoal",
        "challenger_top4": "Benchmark Challenger",
        "strategic": "Execução estratégica",
        "contest": "Contestação",
        "flex": "Flexibilidade",
    }

    @classmethod
    def explain_top4(
        cls,
        *,
        historical_top4: float,
        challenger_top4: float,
        strategic_score: float,
        contest_score: float,
        flex_score: float,
        baseline_probability: float,
        final_probability: float,
    ) -> FeatureImportanceReport:
        values = {
            "historical_top4": historical_top4,
            "challenger_top4": challenger_top4,
            "strategic": strategic_score,
            "contest": contest_score,
            "flex": flex_score,
        }

        raw = {
            name: (value - 50.0) * cls.WEIGHTS[name]
            for name, value in values.items()
        }

        total_raw = sum(raw.values())
        target_delta = final_probability - baseline_probability
        scale = target_delta / total_raw if abs(total_raw) > 0.0001 else 0.0

        contributions = []
        for name, value in values.items():
            contribution = raw[name] * scale
            direction = (
                "positive" if contribution > 0.25
                else "negative" if contribution < -0.25
                else "neutral"
            )
            signal = "favorece" if direction == "positive" else (
                "reduz" if direction == "negative" else "tem efeito neutro em"
            )
            contributions.append(
                FeatureContribution(
                    feature=name,
                    value=round(value, 2),
                    contribution=round(contribution, 2),
                    direction=direction,
                    explanation=(
                        f"{cls.LABELS[name]} {signal} a chance estimada de Top 4."
                    ),
                )
            )

        contributions.sort(
            key=lambda item: abs(item.contribution),
            reverse=True,
        )

        return FeatureImportanceReport(
            baseline_probability=round(baseline_probability, 2),
            final_probability=round(final_probability, 2),
            contributions=tuple(contributions),
        )
