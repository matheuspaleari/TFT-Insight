from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GlobalPriorityResult:
    primary: dict[str, Any] | None
    adjustments: list[dict[str, Any]]
    strengths: list[dict[str, Any]]
    ordered_messages: list[dict[str, Any]]


def _as_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _benchmark_score(
    message: dict[str, Any],
) -> float:
    evidence = message.get("evidence", {}) or {}

    gap = abs(
        _as_float(
            evidence.get("relative_gap"),
            0.0,
        )
    )

    percentile = evidence.get("percentile")

    # Gap de benchmark é importante, mas não recebe prioridade absoluta
    # apenas por ser o maior desvio percentual.
    score = 45.0 + min(gap, 30.0) * 1.5

    if percentile is not None:
        percentile_value = _as_float(
            percentile,
            50.0,
        )

        if percentile_value <= 20.0:
            score += 8.0
        elif percentile_value <= 35.0:
            score += 4.0

    return min(score, 98.0)


def _strategic_score(
    message: dict[str, Any],
) -> float:
    evidence = message.get("evidence", {}) or {}

    score = _as_float(
        message.get("strategic_weight"),
        50.0,
    )

    confidence = _as_float(
        evidence.get("confidence"),
        0.0,
    )

    # Confiança melhora a força de uma conclusão já existente;
    # ela nunca cria uma prioridade por conta própria.
    score += min(confidence, 100.0) * 0.08

    impact_label = str(
        evidence.get(
            "placement_impact_label",
            "",
        )
    ).strip().lower()

    impact_bonus = {
        "alto": 14.0,
        "relevante": 9.0,
        "leve": 2.0,
        "neutro": 0.0,
        "sem_piora_observada": -8.0,
        "indeterminado": -4.0,
    }

    score += impact_bonus.get(
        impact_label,
        0.0,
    )

    return max(
        0.0,
        min(score, 120.0),
    )


def _candidate_score(
    message: dict[str, Any],
) -> float:
    source = message.get(
        "source",
        "strategic",
    )

    if source == "benchmark":
        return _benchmark_score(
            message
        )

    return _strategic_score(
        message
    )


def _normalize_message(
    message: dict[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    normalized = dict(
        message
    )
    normalized["source"] = source
    normalized["global_score"] = round(
        _candidate_score(
            normalized
        ),
        2,
    )
    return normalized


def build_global_priority(
    *,
    strategic_messages: list[dict[str, Any]],
    benchmark_messages: list[dict[str, Any]],
    max_adjustments: int = 2,
    max_strengths: int = 2,
) -> GlobalPriorityResult:
    """
    Orquestra conclusões já produzidas pelos engines.

    Esta camada NÃO cria uma nova análise de TFT. Ela apenas decide qual
    conclusão aprovada deve receber maior atenção no produto, usando:
    - peso estratégico já definido;
    - confiança já calculada;
    - impacto semântico já classificado;
    - magnitude do gap de benchmark.

    O Ollama não participa desta decisão.
    """
    strategic = [
        _normalize_message(
            item,
            source="strategic",
        )
        for item in strategic_messages
    ]

    benchmark = [
        _normalize_message(
            item,
            source="benchmark",
        )
        for item in benchmark_messages
    ]

    candidates = [
        item
        for item in strategic + benchmark
        if item.get("role") in {
            "priority",
            "adjustment",
        }
    ]

    candidates.sort(
        key=lambda item: (
            item.get(
                "global_score",
                0.0,
            ),
            1
            if item.get("source") == "strategic"
            else 0,
        ),
        reverse=True,
    )

    primary = (
        dict(candidates[0])
        if candidates
        else None
    )

    if primary is not None:
        primary["role"] = "priority"
        primary["priority"] = 1

    adjustments: list[
        dict[str, Any]
    ] = []

    for candidate in candidates[1:]:
        item = dict(
            candidate
        )
        item["role"] = "adjustment"
        item["priority"] = 2
        adjustments.append(
            item
        )

        if len(adjustments) >= max_adjustments:
            break

    strengths = [
        dict(item)
        for item in strategic + benchmark
        if item.get("role") == "strength"
    ]

    strengths.sort(
        key=lambda item: item.get(
            "global_score",
            0.0,
        ),
        reverse=True,
    )

    strengths = strengths[
        :max_strengths
    ]

    for item in strengths:
        item["role"] = "strength"
        item["priority"] = None

    ordered = (
        ([primary] if primary else [])
        + adjustments
        + strengths
    )

    return GlobalPriorityResult(
        primary=primary,
        adjustments=adjustments,
        strengths=strengths,
        ordered_messages=ordered,
    )
