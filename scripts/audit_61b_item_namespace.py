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
OBSERVATIONS_PATH = STATE_DIRECTORY / "item_observations.json"
OUTPUT_CSV_PATH = STATE_DIRECTORY / "audit_61b_item_namespace.csv"
OUTPUT_JSON_PATH = STATE_DIRECTORY / "audit_61b_item_namespace.json"


def normalize_item_id(value: str) -> str:
    """
    Normalização APENAS para diagnóstico de namespace.

    Não altera os IDs do projeto e não deve ser usada como lookup oficial
    sem validação posterior.
    """
    text = str(value or "").strip().casefold()

    # Remove separadores para comparar sufixos de namespaces diferentes.
    text = re.sub(r"[^a-z0-9]", "", text)

    # Prefixos comuns encontrados em dados TFT/Riot/CommunityDragon.
    prefixes = (
        "tftitem",
        "tft18item",
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
            if text.startswith(prefix) and len(text) > len(prefix):
                text = text[len(prefix):]
                changed = True
                break

    return text


def load_cached_match_item_counts() -> Counter[str]:
    counts: Counter[str] = Counter()

    if not MATCH_CACHE_DIRECTORY.exists():
        return counts

    for path in sorted(MATCH_CACHE_DIRECTORY.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

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

    return counts


def load_observations() -> dict[str, dict[str, Any]]:
    if not OBSERVATIONS_PATH.exists():
        return {}

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
            "Cache do CommunityDragon não encontrado. "
            "Rode primeiro o benchmark que já baixa esse catálogo."
        )

    payload = repository.load()
    items = CommunityDragonItemParser.parse(payload)

    if not items:
        raise RuntimeError(
            "Nenhum item foi extraído do cache CommunityDragon."
        )

    return items


def observation_role_totals(
    observations: dict[str, dict[str, Any]],
) -> tuple[int, int, int, int]:
    total = 0
    carry = 0
    tank = 0
    support = 0

    for value in observations.values():
        c = int(value.get("damage_carry_uses", 0) or 0)
        t = int(value.get("tank_uses", 0) or 0)
        s = int(value.get("support_uses", 0) or 0)

        carry += c
        tank += t
        support += s
        total += c + t + s

    return total, carry, tank, support


def rich_item_name(item: Any) -> str:
    return str(getattr(item, "name", "") or "").strip()


def build_normalized_index(
    rich_items: dict[str, Any],
) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}

    for item_id in rich_items:
        normalized = normalize_item_id(item_id)
        if not normalized:
            continue
        index.setdefault(normalized, []).append(item_id)

    return index


def main() -> None:
    print("=" * 110)
    print("TFT INSIGHT — #61B ITEM NAMESPACE / OBSERVATION DIAGNOSTIC")
    print("=" * 110)

    raw_counts = load_cached_match_item_counts()
    observations = load_observations()
    rich_items = load_rich_items()

    raw_ids = set(raw_counts)
    observation_ids = set(observations)
    rich_ids = set(rich_items)

    raw_obs_overlap = raw_ids & observation_ids
    obs_rich_overlap = observation_ids & rich_ids
    raw_rich_overlap = raw_ids & rich_ids

    total_role_uses, carry_uses, tank_uses, support_uses = (
        observation_role_totals(observations)
    )

    normalized_rich = build_normalized_index(rich_items)

    normalized_candidates: dict[str, list[str]] = {}
    for item_id in sorted(observation_ids):
        normalized = normalize_item_id(item_id)
        candidates = normalized_rich.get(normalized, [])
        if candidates:
            normalized_candidates[item_id] = candidates

    print(f"Partidas em cache             : {len(list(MATCH_CACHE_DIRECTORY.glob('*.json')))}")
    print(f"IDs de item no cache bruto    : {len(raw_ids)}")
    print(f"Usos de item no cache bruto   : {sum(raw_counts.values())}")
    print(f"IDs em item_observations      : {len(observation_ids)}")
    print(f"IDs no CommunityDragon        : {len(rich_ids)}")
    print()
    print(f"Overlap bruto ↔ observações   : {len(raw_obs_overlap)}")
    print(f"Overlap observações ↔ CDragon : {len(obs_rich_overlap)}")
    print(f"Overlap bruto ↔ CDragon       : {len(raw_rich_overlap)}")
    print(f"Matches normalizados candidatos: {len(normalized_candidates)}")
    print()
    print(f"Usos classificados por role  : {total_role_uses}")
    print(f"  Carry                       : {carry_uses}")
    print(f"  Tank                        : {tank_uses}")
    print(f"  Support                     : {support_uses}")

    # Diagnóstico principal.
    print()
    if observation_ids and total_role_uses > 0:
        print(
            "OK: o UnitRoleSeedInference está gerando observações. "
            "Logo, 'Itens observados: 0' do runner NÃO significa necessariamente "
            "que o collector ficou vazio."
        )
    else:
        print(
            "ATENÇÃO: item_observations.json realmente está vazio ou sem usos por role. "
            "Nesse caso o problema continua antes da etapa de classificação do catálogo."
        )

    if observation_ids and not obs_rich_overlap:
        print(
            "DIAGNÓSTICO FORTE: há observações, mas nenhum ID observado bate "
            "exatamente com as chaves do CommunityDragon."
        )
    elif obs_rich_overlap:
        print(
            "Há IDs observados que batem exatamente com o CommunityDragon; "
            "o problema pode estar no ItemCatalogClassifier ou nos filtros seguintes."
        )

    rows: list[dict[str, Any]] = []

    all_ids = sorted(
        raw_ids | observation_ids,
        key=lambda item_id: (
            -raw_counts.get(item_id, 0),
            item_id,
        ),
    )

    for item_id in all_ids:
        obs = observations.get(item_id, {})
        exact_rich = rich_items.get(item_id)

        candidates = normalized_candidates.get(item_id, [])
        candidate_id = candidates[0] if len(candidates) == 1 else ""
        candidate_item = rich_items.get(candidate_id) if candidate_id else None

        rows.append(
            {
                "riot_item_id": item_id,
                "raw_uses": raw_counts.get(item_id, 0),
                "observed": item_id in observation_ids,
                "carry_uses": int(obs.get("damage_carry_uses", 0) or 0),
                "tank_uses": int(obs.get("tank_uses", 0) or 0),
                "support_uses": int(obs.get("support_uses", 0) or 0),
                "exact_communitydragon_match": exact_rich is not None,
                "exact_name": rich_item_name(exact_rich) if exact_rich else "",
                "normalized_id": normalize_item_id(item_id),
                "normalized_candidate_count": len(candidates),
                "normalized_candidate_id": candidate_id,
                "normalized_candidate_name": (
                    rich_item_name(candidate_item)
                    if candidate_item is not None
                    else ""
                ),
            }
        )

    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys()) if rows else [
                "riot_item_id",
                "raw_uses",
                "observed",
                "carry_uses",
                "tank_uses",
                "support_uses",
                "exact_communitydragon_match",
                "exact_name",
                "normalized_id",
                "normalized_candidate_count",
                "normalized_candidate_id",
                "normalized_candidate_name",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "cached_matches": len(
            list(MATCH_CACHE_DIRECTORY.glob("*.json"))
        ),
        "raw_unique_item_ids": len(raw_ids),
        "raw_item_uses": sum(raw_counts.values()),
        "observation_ids": len(observation_ids),
        "communitydragon_ids": len(rich_ids),
        "raw_observation_overlap": len(raw_obs_overlap),
        "observation_communitydragon_overlap": len(obs_rich_overlap),
        "raw_communitydragon_overlap": len(raw_rich_overlap),
        "normalized_candidate_matches": len(normalized_candidates),
        "role_uses_total": total_role_uses,
        "role_uses_carry": carry_uses,
        "role_uses_tank": tank_uses,
        "role_uses_support": support_uses,
    }

    OUTPUT_JSON_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("-" * 110)
    print("TOP 30 IDs observados")
    print("-" * 110)
    print(
        f"{'RIOT ITEM ID':<48} "
        f"{'USOS':>6} "
        f"{'CARRY':>7} "
        f"{'TANK':>7} "
        f"{'SUP':>7} "
        f"{'EXATO':>6} "
        f"NOME/CANDIDATO"
    )

    for row in rows[:30]:
        shown_name = (
            row["exact_name"]
            or row["normalized_candidate_name"]
            or "-"
        )
        print(
            f"{row['riot_item_id'][:47]:<48} "
            f"{row['raw_uses']:>6} "
            f"{row['carry_uses']:>7} "
            f"{row['tank_uses']:>7} "
            f"{row['support_uses']:>7} "
            f"{('SIM' if row['exact_communitydragon_match'] else 'NÃO'):>6} "
            f"{shown_name[:40]}"
        )

    print()
    print(f"CSV completo : {OUTPUT_CSV_PATH}")
    print(f"Resumo JSON  : {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
