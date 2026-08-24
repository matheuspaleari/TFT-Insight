from __future__ import annotations

from datetime import datetime
from typing import Any

from src.training.models.skill_training_history import (
    SkillTrainingCycleSummary,
    SkillTrainingHistory,
)


class SkillTrainingHistoryAggregator:
    """
    Agrega ciclos arquivados por Skill.

    Esta V1 não recalcula Before/After e não mistura métricas de tasks
    diferentes. Ela resume somente resultados já persistidos em cada ciclo.
    """

    RESULT_SIGNAL: dict[str, int] = {
        "NEGATIVE": -1,
        "STABLE": 0,
        "POSITIVE": 1,
    }

    @classmethod
    def aggregate(
        cls,
        *,
        skill_id: str,
        training_history: list[dict[str, Any]],
    ) -> SkillTrainingHistory:
        normalized_skill_id = str(
            skill_id
        ).strip()

        if not normalized_skill_id:
            raise ValueError(
                "skill_id não pode ser vazio."
            )

        cycles = [
            cls._summarize_cycle(cycle)
            for cycle in training_history
            if cls._cycle_skill_id(cycle)
            == normalized_skill_id
        ]

        # Quando timestamps existem, usa ordem temporal real.
        # Se não existem, preserva a ordem recebida pelo repository.
        cycles = cls._sort_cycles(
            cycles
        )

        evaluated = tuple(
            cycle
            for cycle in cycles
            if cycle.result is not None
        )

        conclusive = tuple(
            cycle
            for cycle in evaluated
            if cycle.is_conclusive
        )

        positive = sum(
            cycle.result == "POSITIVE"
            for cycle in evaluated
        )
        stable = sum(
            cycle.result == "STABLE"
            for cycle in evaluated
        )
        negative = sum(
            cycle.result == "NEGATIVE"
            for cycle in evaluated
        )
        inconclusive = sum(
            cycle.result == "INCONCLUSIVE"
            for cycle in evaluated
        )

        trend, confidence, rationale = (
            SkillTrainingTrendEngine.evaluate(
                conclusive_cycles=conclusive,
                evaluated_cycles=evaluated,
            )
        )

        latest_result = (
            evaluated[0].result
            if evaluated
            else None
        )

        previous_result = (
            evaluated[1].result
            if len(evaluated) >= 2
            else None
        )

        return SkillTrainingHistory(
            skill_id=normalized_skill_id,
            cycles_total=len(cycles),
            evaluated_cycles=len(evaluated),
            conclusive_cycles=len(conclusive),
            positive_cycles=positive,
            stable_cycles=stable,
            negative_cycles=negative,
            inconclusive_cycles=inconclusive,
            trend=trend,
            trend_confidence=confidence,
            latest_result=latest_result,
            previous_result=previous_result,
            cycles=tuple(cycles),
            rationale=rationale,
        )

    @classmethod
    def aggregate_all(
        cls,
        *,
        training_history: list[dict[str, Any]],
    ) -> dict[str, SkillTrainingHistory]:
        skill_ids = tuple(
            dict.fromkeys(
                skill_id
                for skill_id in (
                    cls._cycle_skill_id(cycle)
                    for cycle in training_history
                )
                if skill_id
            )
        )

        return {
            skill_id: cls.aggregate(
                skill_id=skill_id,
                training_history=training_history,
            )
            for skill_id in skill_ids
        }

    @classmethod
    def _summarize_cycle(
        cls,
        cycle: dict[str, Any],
    ) -> SkillTrainingCycleSummary:
        mission = cycle.get(
            "mission",
            {},
        )

        if not isinstance(
            mission,
            dict,
        ):
            mission = {}

        task = mission.get(
            "task",
            {},
        )

        if not isinstance(
            task,
            dict,
        ):
            task = {}

        evaluation = cycle.get(
            "evaluation",
            {},
        )

        if not isinstance(
            evaluation,
            dict,
        ):
            evaluation = {}

        result_raw = str(
            evaluation.get(
                "result",
                "",
            )
        ).strip().upper()

        result = (
            result_raw
            if result_raw
            else None
        )

        signal = (
            cls.RESULT_SIGNAL.get(
                result
            )
            if result
            else None
        )

        confidence = str(
            evaluation.get(
                "confidence",
                "",
            )
        ).strip().upper() or None

        confidence_score_raw = (
            evaluation.get(
                "confidence_score"
            )
        )

        confidence_score = (
            float(confidence_score_raw)
            if isinstance(
                confidence_score_raw,
                (int, float),
            )
            else None
        )

        evaluated_at = str(
            evaluation.get(
                "evaluated_at",
                "",
            )
            or cycle.get(
                "archived_at",
                "",
            )
            or cycle.get(
                "completed_at",
                "",
            )
            or ""
        ).strip() or None

        return SkillTrainingCycleSummary(
            cycle_id=str(
                cycle.get(
                    "cycle_id",
                    mission.get(
                        "mission_id",
                        "",
                    ),
                )
            ),
            skill_id=str(
                task.get(
                    "skill_id",
                    "",
                )
            ),
            task_id=(
                str(
                    task.get(
                        "id",
                        "",
                    )
                ).strip()
                or None
            ),
            task_title=(
                str(
                    task.get(
                        "title",
                        mission.get(
                            "title",
                            "",
                        ),
                    )
                ).strip()
                or None
            ),
            result=result,
            confidence=confidence,
            confidence_score=confidence_score,
            evaluated_at=evaluated_at,
            is_conclusive=signal is not None,
            signal=signal,
        )

    @staticmethod
    def _cycle_skill_id(
        cycle: dict[str, Any],
    ) -> str | None:
        if not isinstance(
            cycle,
            dict,
        ):
            return None

        mission = cycle.get(
            "mission",
            {},
        )

        if not isinstance(
            mission,
            dict,
        ):
            return None

        task = mission.get(
            "task",
            {},
        )

        if not isinstance(
            task,
            dict,
        ):
            return None

        value = str(
            task.get(
                "skill_id",
                "",
            )
        ).strip()

        return value or None

    @staticmethod
    def _parse_timestamp(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            return None

    @classmethod
    def _sort_cycles(
        cls,
        cycles: list[SkillTrainingCycleSummary],
    ) -> list[SkillTrainingCycleSummary]:
        if not cycles:
            return []

        parsed = [
            cls._parse_timestamp(
                cycle.evaluated_at
            )
            for cycle in cycles
        ]

        if not any(
            value is not None
            for value in parsed
        ):
            return cycles

        indexed = list(
            enumerate(cycles)
        )

        indexed.sort(
            key=lambda item: (
                cls._parse_timestamp(
                    item[1].evaluated_at
                )
                or datetime.min.replace(
                    tzinfo=None
                ),
                -item[0],
            ),
            reverse=True,
        )

        return [
            cycle
            for _, cycle in indexed
        ]


class SkillTrainingTrendEngine:
    """
    Classifica tendência usando resultados persistidos de ciclos da mesma Skill.

    A V1 exige ao menos 2 ciclos CONCLUSIVOS.
    INCONCLUSIVE não gera sinal e não é usado para inventar tendência.

    Regra com os dois ciclos conclusivos mais recentes:
    - sinal mais recente > anterior  -> IMPROVING
    - sinal mais recente < anterior  -> REGRESSING
    - sinais iguais:
        POSITIVE + POSITIVE -> IMPROVING
        STABLE + STABLE     -> STABLE
        NEGATIVE + NEGATIVE -> REGRESSING

    Isso representa tendência dos resultados de treino, não causalidade
    nem evolução definitiva da Skill.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        conclusive_cycles: tuple[
            SkillTrainingCycleSummary,
            ...
        ],
        evaluated_cycles: tuple[
            SkillTrainingCycleSummary,
            ...
        ],
    ) -> tuple[str, str, str]:
        if len(
            conclusive_cycles
        ) < 2:
            return (
                "INSUFFICIENT_HISTORY",
                "LOW",
                (
                    "Ainda não existem pelo menos dois ciclos conclusivos "
                    "da mesma Skill. Não há histórico suficiente para "
                    "classificar uma tendência."
                ),
            )

        latest = conclusive_cycles[0]
        previous = conclusive_cycles[1]

        latest_signal = int(
            latest.signal
            if latest.signal is not None
            else 0
        )
        previous_signal = int(
            previous.signal
            if previous.signal is not None
            else 0
        )

        if latest_signal > previous_signal:
            trend = "IMPROVING"
        elif latest_signal < previous_signal:
            trend = "REGRESSING"
        elif latest_signal > 0:
            trend = "IMPROVING"
        elif latest_signal < 0:
            trend = "REGRESSING"
        else:
            trend = "STABLE"

        confidence = cls._confidence(
            conclusive_cycles=conclusive_cycles,
            evaluated_cycles=evaluated_cycles,
        )

        rationale = (
            f"Os dois ciclos conclusivos mais recentes passaram de "
            f"{previous.result} para {latest.result}. "
            f"A tendência {trend} descreve a sequência observada nos ciclos "
            "de treino da Skill e não prova causalidade."
        )

        return (
            trend,
            confidence,
            rationale,
        )

    @staticmethod
    def _confidence(
        *,
        conclusive_cycles: tuple[
            SkillTrainingCycleSummary,
            ...
        ],
        evaluated_cycles: tuple[
            SkillTrainingCycleSummary,
            ...
        ],
    ) -> str:
        conclusive_count = len(
            conclusive_cycles
        )

        if conclusive_count >= 4:
            return "HIGH"

        if conclusive_count >= 2:
            return "MODERATE"

        return "LOW"
