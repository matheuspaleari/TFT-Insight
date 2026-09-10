from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.role_inference import RichItemRepository, CommunityDragonItemParser


STATE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "challenger"
)

MATCH_CACHE_DIRECTORY = STATE_DIRECTORY / "matches"
MATCH_INDEX_PATH = STATE_DIRECTORY / "match_index.json"
OBSERVATIONS_PATH = STATE_DIRECTORY / "item_observations.json"

OUTPUT_CSV_PATH = (
    STATE_DIRECTORY
    / "audit_61c_observed_items.csv"
)

OUTPUT_JSON_PATH = (
    STATE_DIRECTORY
    / "audit_61c_observed_items.json"
)


def normalize_item_id(value: str) -> str:
    """
    Normalização usada somente para sugerir candidatos equivalentes
    entre namespaces. Não altera IDs internos do projeto.
    """
    text = str(value or "").strip().casefold()
    text = re.sub(r"[^a-z0-9]", "", text)

    prefixes = (
        "tft18item",
        "tftitem",
        "tft18",
        "tft",
        "daartifact",
        "daradiant",
        "daitem",
        "da",
    )

    changed = True

    while changed and text:
        changed = False

        for prefix in prefixes:
            if (
                text.startswith(prefix)
                and len(text) > len(prefix)
            ):
                text = text[len(prefix):]
                changed = True
                break

    return text


def load_index() -> dict[str, Any]:
    if not MATCH_INDEX_PATH.exists():
        raise RuntimeError(
            f"Índice Challenger não encontrado: {MATCH_INDEX_PATH}"
        )

    payload = json.loads(
        MATCH_INDEX_PATH.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise RuntimeError(
            "match_index.json possui formato inválido."
        )

    return payload


def current_benchmark_match_ids(
    index: dict[str, Any],
) -> list[str]:
    raw = index.get("match_ids", {})

    if not isinstance(raw, dict) or not raw:
        raise RuntimeError(
            "match_index.json não possui match_ids válidos."
        )

    return [
        str(match_id)
        for match_id in raw.keys()
    ]


def load_current_match_item_counts(
    match_ids: list[str],
) -> tuple[Counter[str], int, list[str]]:
    counts: Counter[str] = Counter()
    cached_count = 0
    missing_cache: list[str] = []

    for match_id in match_ids:
        path = MATCH_CACHE_DIRECTORY / f"{match_id}.json"

        if not path.exists():
            missing_cache.append(match_id)
            continue

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            missing_cache.append(match_id)
            continue

        cached_count += 1

        info = payload.get("info")
        if not isinstance(info, dict):
            continue

        participants = info.get("participants")
        if not isinstance(participants, list):
            continue

        for participant in participants:
            if not isinstance(participant, dict):
                continue

            units = participant.get("units")
            if not isinstance(units, list):
                continue

            for unit in units:
                if not isinstance(unit, dict):
                    continue

                item_names = unit.get("itemNames")
                if not isinstance(item_names, list):
                    continue

                for item_id in item_names:
                    item_id = str(item_id or "").strip()

                    if item_id:
                        counts[item_id] += 1

    return counts, cached_count, missing_cache


def load_observations() -> dict[str, dict[str, Any]]:
    if not OBSERVATIONS_PATH.exists():
        raise RuntimeError(
            f"Observações não encontradas: {OBSERVATIONS_PATH}"
        )

    raw = json.loads(
        OBSERVATIONS_PATH.read_text(encoding="utf-8")
    )

    if not isinstance(raw, dict):
        raise RuntimeError(
            "item_observations.json possui formato inesperado."
        )

    return {
        str(item_id): value
        for item_id, value in raw.items()
        if isinstance(value, dict)
    }


def load_rich_items() -> dict[str, Any]:
    repository = RichItemRepository()

    if not repository.exists():
        raise RuntimeError(
            "Cache do CommunityDragon não encontrado."
        )

    payload = repository.load()
    items = CommunityDragonItemParser.parse(payload)

    if not items:
        raise RuntimeError(
            "Nenhum item foi extraído do CommunityDragon."
        )

    return items


def rich_item_name(item: Any) -> str:
    return str(
        getattr(item, "name", "")
        or ""
    ).strip()


def build_normalized_index(
    rich_items: dict[str, Any],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}

    for item_id in rich_items:
        normalized = normalize_item_id(item_id)

        if normalized:
            result.setdefault(
                normalized,
                [],
            ).append(item_id)

    return result


def observation_uses(
    observation: dict[str, Any],
) -> tuple[int, int, int, int]:
    carry = int(
        observation.get(
            "damage_carry_uses",
            0,
        )
        or 0
    )

    tank = int(
        observation.get(
            "tank_uses",
            0,
        )
        or 0
    )

    support = int(
        observation.get(
            "support_uses",
            0,
        )
        or 0
    )

    return (
        carry + tank + support,
        carry,
        tank,
        support,
    )


def main() -> None:
    print("=" * 110)
    print(
        "TFT INSIGHT — #61C OBSERVED ITEMS / CURRENT BENCHMARK ONLY"
    )
    print("=" * 110)

    index = load_index()
    benchmark_match_ids = current_benchmark_match_ids(index)

    (
        raw_counts,
        cached_count,
        missing_cache,
    ) = load_current_match_item_counts(
        benchmark_match_ids
    )

    observations = load_observations()
    rich_items = load_rich_items()

    normalized_rich = build_normalized_index(
        rich_items
    )

    rows: list[dict[str, Any]] = []

    for item_id, observation in observations.items():
        (
            observed_uses,
            carry_uses,
            tank_uses,
            support_uses,
        ) = observation_uses(observation)

        normalized = normalize_item_id(item_id)
        candidates = normalized_rich.get(
            normalized,
            [],
        )

        exact_item = rich_items.get(item_id)

        candidate_id = (
            candidates[0]
            if len(candidates) == 1
            else ""
        )

        candidate_item = (
            rich_items.get(candidate_id)
            if candidate_id
            else None
        )

        display_name = (
            rich_item_name(exact_item)
            if exact_item is not None
            else (
                rich_item_name(candidate_item)
                if candidate_item is not None
                else ""
            )
        )

        rows.append(
            {
                "riot_item_id": item_id,
                "benchmark_raw_uses": raw_counts.get(
                    item_id,
                    0,
                ),
                "observed_uses": observed_uses,
                "carry_uses": carry_uses,
                "tank_uses": tank_uses,
                "support_uses": support_uses,
                "display_name_candidate": display_name,
                "exact_communitydragon_match": (
                    exact_item is not None
                ),
                "normalized_candidate_count": len(
                    candidates
                ),
                "normalized_candidate_id": (
                    candidate_id
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            row["observed_uses"],
            row["benchmark_raw_uses"],
            row["riot_item_id"],
        ),
        reverse=True,
    )

    OUTPUT_CSV_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "riot_item_id",
        "benchmark_raw_uses",
        "observed_uses",
        "carry_uses",
        "tank_uses",
        "support_uses",
        "display_name_candidate",
        "exact_communitydragon_match",
        "normalized_candidate_count",
        "normalized_candidate_id",
    ]

    with OUTPUT_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "benchmark_match_ids": len(
            benchmark_match_ids
        ),
        "benchmark_cached_matches": cached_count,
        "missing_cached_matches": len(
            missing_cache
        ),
        "raw_unique_item_ids_current_benchmark": len(
            raw_counts
        ),
        "raw_item_uses_current_benchmark": sum(
            raw_counts.values()
        ),
        "observed_item_ids": len(
            rows
        ),
        "observed_role_uses": sum(
            row["observed_uses"]
            for row in rows
        ),
        "carry_uses": sum(
            row["carry_uses"]
            for row in rows
        ),
        "tank_uses": sum(
            row["tank_uses"]
            for row in rows
        ),
        "support_uses": sum(
            row["support_uses"]
            for row in rows
        ),
        "items_with_name_candidate": sum(
            1
            for row in rows
            if row["display_name_candidate"]
        ),
        "exact_communitydragon_matches": sum(
            1
            for row in rows
            if row["exact_communitydragon_match"]
        ),
        "single_normalized_candidates": sum(
            1
            for row in rows
            if row["normalized_candidate_count"] == 1
        ),
        "output_csv": str(
            OUTPUT_CSV_PATH
        ),
    }

    OUTPUT_JSON_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"IDs do benchmark atual       : "
        f"{summary['benchmark_match_ids']}"
    )
    print(
        f"Partidas encontradas no cache: "
        f"{summary['benchmark_cached_matches']}"
    )
    print(
        f"Partidas ausentes no cache   : "
        f"{summary['missing_cached_matches']}"
    )
    print(
        f"IDs de item no benchmark     : "
        f"{summary['raw_unique_item_ids_current_benchmark']}"
    )
    print(
        f"Usos brutos no benchmark     : "
        f"{summary['raw_item_uses_current_benchmark']}"
    )
    print()
    print(
        f"IDs realmente observados     : "
        f"{summary['observed_item_ids']}"
    )
    print(
        f"Usos aprendidos por role     : "
        f"{summary['observed_role_uses']}"
    )
    print(
        f"  Carry                      : "
        f"{summary['carry_uses']}"
    )
    print(
        f"  Tank                       : "
        f"{summary['tank_uses']}"
    )
    print(
        f"  Support                    : "
        f"{summary['support_uses']}"
    )
    print()
    print(
        f"Com candidato de nome        : "
        f"{summary['items_with_name_candidate']}"
    )
    print(
        f"Match exato CommunityDragon  : "
        f"{summary['exact_communitydragon_matches']}"
    )
    print(
        f"Candidato normalizado único  : "
        f"{summary['single_normalized_candidates']}"
    )

    print()
    print("-" * 110)
    print("TOP 30 — SOMENTE ITENS REALMENTE OBSERVADOS")
    print("-" * 110)

    print(
        f"{'RIOT ITEM ID':<44} "
        f"{'OBS':>6} "
        f"{'CARRY':>7} "
        f"{'TANK':>7} "
        f"{'SUP':>7} "
        f"NOME CANDIDATO"
    )

    for row in rows[:30]:
        print(
            f"{row['riot_item_id'][:43]:<44} "
            f"{row['observed_uses']:>6} "
            f"{row['carry_uses']:>7} "
            f"{row['tank_uses']:>7} "
            f"{row['support_uses']:>7} "
            f"{(row['display_name_candidate'] or '-')[:40]}"
        )

    print()
    print(f"CSV observado : {OUTPUT_CSV_PATH}")
    print(f"Resumo JSON   : {OUTPUT_JSON_PATH}")

    if missing_cache:
        print()
        print(
            "ATENÇÃO: existem partidas do índice atual sem JSON "
            "válido no cache."
        )


if __name__ == "__main__":
    main()
