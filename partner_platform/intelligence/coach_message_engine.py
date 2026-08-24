from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from .coach_messages import (
    COACH_MESSAGE_LIBRARY,
    GENERIC_MESSAGES,
)


@dataclass(frozen=True)
class CoachEvidence:
    player_value: float | None
    benchmark_value: float | None
    relative_gap: float | None
    percentile: float | None


@dataclass(frozen=True)
class CoachMessage:
    role: str
    metric: str
    metric_label: str
    title: str
    message: str
    evidence: CoachEvidence
    priority: int | None = None


def _metric_key(item: dict[str, Any]) -> str:
    return str(
        item.get(
            "metric",
            item.get("label", "unknown"),
        )
    )


def _metric_label(item: dict[str, Any]) -> str:
    return str(
        item.get(
            "label",
            item.get("metric", "Métrica"),
        )
    )


def _benchmark_value(
    item: dict[str, Any],
) -> float | None:
    value = item.get(
        "benchmark_mean",
        item.get("challenger_mean"),
    )

    if value is None:
        return None

    return float(value)


def _relative_gap(
    item: dict[str, Any],
) -> float | None:
    benchmark_value = _benchmark_value(
        item
    )

    if benchmark_value in (
        None,
        0,
    ):
        return None

    performance_delta = float(
        item.get(
            "performance_delta",
            0.0,
        )
    )

    return (
        performance_delta
        / abs(benchmark_value)
        * 100.0
    )


def _competitive_score(
    item: dict[str, Any],
) -> float:
    percentile = item.get(
        "percentile"
    )

    if percentile is not None:
        return (
            float(percentile)
            - 50.0
        )

    gap = _relative_gap(
        item
    )

    if gap is not None:
        return gap

    return float(
        item.get(
            "performance_delta",
            0.0,
        )
    )


def _stable_choice(
    options: tuple[str, ...],
    *,
    seed: str,
) -> str:
    if not options:
        return ""

    digest = hashlib.sha256(
        seed.encode("utf-8")
    ).digest()

    index = int.from_bytes(
        digest[:4],
        "big",
    ) % len(options)

    return options[index]


def _message_template(
    metric: str,
    key: str,
    *,
    seed: str,
) -> str:
    metric_messages = (
        COACH_MESSAGE_LIBRARY.get(
            metric,
            {},
        )
    )

    options = metric_messages.get(
        key
    )

    if not options:
        options = GENERIC_MESSAGES[
            key
        ]

    return _stable_choice(
        options,
        seed=seed,
    )


def _build_message(
    item: dict[str, Any],
    *,
    role: str,
    benchmark_name: str,
    priority: int | None,
) -> CoachMessage:
    metric = _metric_key(
        item
    )
    label = _metric_label(
        item
    )
    gap = _relative_gap(
        item
    )
    percentile_raw = item.get(
        "percentile"
    )
    percentile = (
        float(percentile_raw)
        if percentile_raw is not None
        else None
    )

    is_strength = role == "strength"

    key_prefix = (
        "strength"
        if is_strength
        else "priority"
    )

    seed_base = (
        f"{metric}|{benchmark_name}|"
        f"{round(gap or 0.0, 1)}|{role}"
    )

    title = _message_template(
        metric,
        f"{key_prefix}_title",
        seed=seed_base + "|title",
    )

    message = _message_template(
        metric,
        f"{key_prefix}_body",
        seed=seed_base + "|body",
    )

    if is_strength:
        message = (
            message
            + f" A referência ativa é {benchmark_name}."
        )
    else:
        message = (
            message
            + f" Compare novamente com {benchmark_name} depois de aumentar "
            "a amostra para verificar se esse foco está trazendo resultado."
        )

    return CoachMessage(
        role=role,
        metric=metric,
        metric_label=label,
        title=title,
        message=message,
        evidence=CoachEvidence(
            player_value=(
                float(
                    item["player_value"]
                )
                if item.get(
                    "player_value"
                )
                is not None
                else None
            ),
            benchmark_value=_benchmark_value(
                item
            ),
            relative_gap=gap,
            percentile=percentile,
        ),
        priority=priority,
    )


def build_coach_messages(
    comparison: dict[str, Any],
    *,
    benchmark_name: str,
    max_priorities: int = 2,
    include_strength: bool = True,
) -> list[CoachMessage]:
    """
    Converte resultados já calculados pelo TFT Insight em mensagens-base
    de coaching.

    Esta camada NÃO recalcula o benchmark e NÃO inventa eventos de partida.
    Ela apenas classifica os resultados existentes para selecionar mensagens
    aprovadas pela aplicação.
    """
    comparisons = list(
        comparison.get(
            "comparisons",
            [],
        )
    )

    if not comparisons:
        return []

    ranked = sorted(
        comparisons,
        key=_competitive_score,
    )

    weaknesses = [
        item
        for item in ranked
        if _competitive_score(item) < 0
    ]

    strengths = [
        item
        for item in reversed(ranked)
        if _competitive_score(item) >= 0
    ]

    messages: list[
        CoachMessage
    ] = []

    for index, item in enumerate(
        weaknesses[:max_priorities],
        start=1,
    ):
        messages.append(
            _build_message(
                item,
                role=(
                    "priority"
                    if index == 1
                    else "adjustment"
                ),
                benchmark_name=benchmark_name,
                priority=index,
            )
        )

    if (
        include_strength
        and strengths
    ):
        messages.append(
            _build_message(
                strengths[0],
                role="strength",
                benchmark_name=benchmark_name,
                priority=None,
            )
        )

    return messages


def coach_messages_payload(
    messages: list[
        CoachMessage
    ],
) -> list[dict[str, Any]]:
    """
    Payload seguro que poderá ser enviado futuramente ao narrador local.
    A IA receberá somente mensagens-base e evidências já calculadas.
    """
    return [
        {
            "role": item.role,
            "metric": item.metric,
            "metric_label": item.metric_label,
            "title": item.title,
            "message": item.message,
            "priority": item.priority,
            "evidence": {
                "player_value": item.evidence.player_value,
                "benchmark_value": item.evidence.benchmark_value,
                "relative_gap": item.evidence.relative_gap,
                "percentile": item.evidence.percentile,
            },
        }
        for item in messages
    ]
