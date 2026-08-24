from __future__ import annotations

from collections import defaultdict

from src.coach_intelligence.models.training_effectiveness import (
    TaskEffectiveness,
)


class TrainingEffectivenessEngine:
    """
    Resume resultados observados por exercício.

    Não afirma que o exercício causou melhora/piora.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        training_history: list[dict],
    ) -> tuple[TaskEffectiveness, ...]:
        grouped = defaultdict(
            lambda: {
                "title": "",
                "results": [],
            }
        )

        for cycle in training_history:
            mission = cycle.get(
                "mission",
                {},
            )
            task = mission.get(
                "task",
                {},
            )
            evaluation = cycle.get(
                "evaluation"
            )

            if not isinstance(
                task,
                dict,
            ):
                continue

            skill_id = str(
                task.get(
                    "skill_id",
                    "",
                )
            )
            task_id = str(
                task.get(
                    "id",
                    "",
                )
            )

            if not skill_id or not task_id:
                continue

            key = (
                skill_id,
                task_id,
            )

            grouped[key]["title"] = str(
                task.get(
                    "title",
                    task_id,
                )
            )

            if isinstance(
                evaluation,
                dict,
            ):
                result = str(
                    evaluation.get(
                        "result",
                        "INCONCLUSIVE",
                    )
                ).upper()
                grouped[key]["results"].append(
                    result
                )

        output = []

        for (
            skill_id,
            task_id,
        ), data in grouped.items():
            results = data[
                "results"
            ]

            positive = results.count(
                "POSITIVE"
            )
            stable = results.count(
                "STABLE"
            )
            negative = results.count(
                "NEGATIVE"
            )
            inconclusive = results.count(
                "INCONCLUSIVE"
            )
            conclusive = (
                positive
                + stable
                + negative
            )

            effectiveness = cls._classify(
                positive=positive,
                stable=stable,
                negative=negative,
                conclusive=conclusive,
            )

            confidence = cls._confidence(
                conclusive
            )

            output.append(
                TaskEffectiveness(
                    skill_id=skill_id,
                    task_id=task_id,
                    task_title=data[
                        "title"
                    ],
                    evaluated_cycles=len(
                        results
                    ),
                    conclusive_cycles=conclusive,
                    positive_cycles=positive,
                    stable_cycles=stable,
                    negative_cycles=negative,
                    inconclusive_cycles=inconclusive,
                    effectiveness=effectiveness,
                    confidence=confidence,
                    rationale=cls._rationale(
                        positive=positive,
                        stable=stable,
                        negative=negative,
                        inconclusive=inconclusive,
                        effectiveness=effectiveness,
                    ),
                )
            )

        return tuple(
            sorted(
                output,
                key=lambda item: (
                    item.skill_id,
                    item.task_id,
                ),
            )
        )

    @staticmethod
    def _classify(
        *,
        positive: int,
        stable: int,
        negative: int,
        conclusive: int,
    ) -> str:
        if conclusive < 2:
            return "INSUFFICIENT_HISTORY"

        if (
            positive >= 2
            and positive > negative
        ):
            return "PROMISING"

        if (
            negative >= 2
            and negative > positive
        ):
            return "LOW_OBSERVED_EFFECTIVENESS"

        if (
            stable >= 2
            and positive == 0
            and negative == 0
        ):
            return "STABLE_EFFECT"

        return "MIXED"

    @staticmethod
    def _confidence(
        conclusive: int,
    ) -> str:
        if conclusive >= 5:
            return "HIGH"

        if conclusive >= 3:
            return "MODERATE"

        return "LOW"

    @staticmethod
    def _rationale(
        *,
        positive: int,
        stable: int,
        negative: int,
        inconclusive: int,
        effectiveness: str,
    ) -> str:
        return (
            f"Resultados observados: +{positive} / ={stable} / "
            f"-{negative} / ?{inconclusive}. "
            f"Classificação: {effectiveness}. "
            "A classificação descreve associação histórica e não "
            "atribui causalidade ao exercício."
        )
