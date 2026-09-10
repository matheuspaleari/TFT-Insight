from __future__ import annotations

import csv
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATCH_CACHE_DIRECTORY = PROJECT_ROOT / "data" / "role_inference" / "challenger" / "matches"

TARGET_SET_NUMBER = 18
TARGET_SET_CORE_NAME = "TFTSet18"

TXT_OUTPUT = PROJECT_ROOT / "set18_unit_catalog_audit.txt"
CSV_OUTPUT = PROJECT_ROOT / "set18_unit_catalog_audit.csv"
JSON_OUTPUT = PROJECT_ROOT / "set18_unit_catalog_audit.json"

TOP_ITEMS = 12
TOP_COMBINATIONS = 8


def is_target_set_match(match_data: dict[str, Any]) -> bool:
    info = match_data.get("info")
    if not isinstance(info, dict):
        return False

    raw_number = info.get("tft_set_number")
    raw_core = str(info.get("tft_set_core_name") or "").strip()

    try:
        if raw_number is not None:
            return int(raw_number) == TARGET_SET_NUMBER
    except (TypeError, ValueError):
        pass

    return raw_core.casefold() == TARGET_SET_CORE_NAME.casefold()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def display_name(character_id: str, raw_name: str) -> str:
    if raw_name.strip():
        return raw_name.strip()

    value = character_id.strip()
    for prefix in ("DA_18_", "TFT18_", "TFT_18_"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break

    return value.replace("_", " ").strip() or character_id


def inferred_cost(rarity: int) -> str:
    # Mantém rarity_raw no relatório. Esta conversão só é aplicada
    # para a faixa básica usual 0..4 => custo 1..5.
    if 0 <= rarity <= 4:
        return str(rarity + 1)
    return "especial/?"


def load_matches() -> tuple[list[dict[str, Any]], list[str], int]:
    if not MATCH_CACHE_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Cache não encontrado: {MATCH_CACHE_DIRECTORY}"
        )

    paths = sorted(MATCH_CACHE_DIRECTORY.glob("*.json"))
    matches = []
    errors = []

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {type(exc).__name__}: {exc}")
            continue

        if isinstance(data, dict) and is_target_set_match(data):
            matches.append(data)

    return matches, errors, len(paths)


def collect(matches: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    units: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "raw_names": Counter(),
            "rarities": Counter(),
            "tiers": Counter(),
            "items": Counter(),
            "combos": Counter(),
            "placements": Counter(),
            "uses": 0,
            "itemized_uses": 0,
            "total_items": 0,
        }
    )

    for match in matches:
        info = match.get("info", {})
        participants = info.get("participants", []) if isinstance(info, dict) else []
        if not isinstance(participants, list):
            continue

        for participant in participants:
            if not isinstance(participant, dict):
                continue

            placement = safe_int(participant.get("placement"), 0)
            raw_units = participant.get("units", [])
            if not isinstance(raw_units, list):
                continue

            for unit in raw_units:
                if not isinstance(unit, dict):
                    continue

                character_id = str(unit.get("character_id") or "").strip()
                if not character_id:
                    continue

                row = units[character_id]
                row["uses"] += 1

                raw_name = str(unit.get("name") or "").strip()
                if raw_name:
                    row["raw_names"][raw_name] += 1

                rarity = safe_int(unit.get("rarity"), -1)
                tier = safe_int(unit.get("tier"), 0)

                row["rarities"][rarity] += 1
                row["tiers"][tier] += 1

                if placement:
                    row["placements"][placement] += 1

                raw_items = unit.get("itemNames", [])
                items = [
                    str(item).strip()
                    for item in raw_items
                    if isinstance(item, str) and item.strip()
                ] if isinstance(raw_items, list) else []

                if items:
                    row["itemized_uses"] += 1

                row["total_items"] += len(items)
                row["items"].update(items)

                if items:
                    row["combos"][tuple(sorted(items))] += 1

    return dict(units)


def common(counter: Counter, fallback: Any) -> Any:
    return counter.most_common(1)[0][0] if counter else fallback


def build_rows(units: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []

    for character_id, stats in units.items():
        uses = int(stats["uses"])
        raw_name = str(common(stats["raw_names"], ""))
        rarity = int(common(stats["rarities"], -1))

        placement_count = sum(stats["placements"].values())
        placement_total = sum(
            placement * count
            for placement, count in stats["placements"].items()
        )

        avg_placement = (
            round(placement_total / placement_count, 2)
            if placement_count
            else None
        )

        top_items = [
            {
                "item_id": item_id,
                "uses": count,
                "rate": round(count / uses * 100.0, 2) if uses else 0.0,
            }
            for item_id, count in stats["items"].most_common(TOP_ITEMS)
        ]

        top_combos = [
            {
                "items": list(combo),
                "uses": count,
            }
            for combo, count in stats["combos"].most_common(TOP_COMBINATIONS)
        ]

        rows.append(
            {
                "character_id": character_id,
                "display_name": display_name(character_id, raw_name),
                "raw_name": raw_name,
                "rarity_raw_mode": rarity,
                "inferred_cost": inferred_cost(rarity),
                "uses": uses,
                "itemized_uses": int(stats["itemized_uses"]),
                "itemized_rate": round(
                    stats["itemized_uses"] / uses * 100.0, 2
                ) if uses else 0.0,
                "average_items": round(
                    stats["total_items"] / uses, 2
                ) if uses else 0.0,
                "average_placement": avg_placement,
                "tier_distribution": {
                    str(k): v for k, v in stats["tiers"].items()
                },
                "rarity_distribution": {
                    str(k): v for k, v in stats["rarities"].items()
                },
                "top_items": top_items,
                "top_item_combinations": top_combos,
            }
        )

    rows.sort(key=lambda row: (-row["uses"], row["character_id"]))
    return rows


def save_reports(
    rows: list[dict[str, Any]],
    matches_count: int,
    cache_count: int,
    errors: list[str],
) -> None:
    lines = [
        "=" * 140,
        "TFT INSIGHT — CATÁLOGO OBSERVADO DE UNIDADES — SET 18",
        "=" * 140,
        "",
        f"JSONs totais no cache        : {cache_count}",
        f"Partidas comprovadas Set 18  : {matches_count}",
        f"Unidades únicas observadas   : {len(rows)}",
        f"Erros de leitura             : {len(errors)}",
        "",
        "IMPORTANTE: inferred_cost usa apenas rarity 0..4 => custo 1..5.",
        "Valores fora dessa faixa ficam como especial/?.",
        "Este relatório NÃO classifica carry/tank/support.",
        "",
        f"{'#':>3}  {'CHARACTER_ID':<36} {'NOME':<24} {'CUSTO':<10} {'RAR':>4} {'USOS':>6} {'ITEM%':>7} {'AVGIT':>6} {'AVGPLC':>7}",
        "-" * 140,
    ]

    for i, row in enumerate(rows, 1):
        avg_plc = "-" if row["average_placement"] is None else f"{row['average_placement']:.2f}"
        lines.append(
            f"{i:>3}  "
            f"{row['character_id']:<36.36} "
            f"{row['display_name']:<24.24} "
            f"{str(row['inferred_cost']):<10.10} "
            f"{row['rarity_raw_mode']:>4} "
            f"{row['uses']:>6} "
            f"{row['itemized_rate']:>6.1f}% "
            f"{row['average_items']:>6.2f} "
            f"{avg_plc:>7}"
        )

    lines.extend(["", "=" * 140, "DETALHE POR UNIDADE", "=" * 140])

    for i, row in enumerate(rows, 1):
        lines.extend(
            [
                "",
                f"[{i:03}] {row['character_id']} — {row['display_name']}",
                "-" * 140,
                f"raw_name             : {row['raw_name'] or '-'}",
                f"rarity_raw_mode       : {row['rarity_raw_mode']}",
                f"custo inferido        : {row['inferred_cost']}",
                f"usos                  : {row['uses']}",
                f"usos itemizados       : {row['itemized_uses']} ({row['itemized_rate']:.2f}%)",
                f"média de itens        : {row['average_items']:.2f}",
                f"colocação média       : {row['average_placement']}",
                f"tiers/estrelas        : {row['tier_distribution']}",
                f"rarity distribution   : {row['rarity_distribution']}",
                "itens mais usados:",
            ]
        )

        if row["top_items"]:
            for item in row["top_items"]:
                lines.append(
                    f"  - {item['item_id']}: {item['uses']} usos "
                    f"({item['rate']:.2f}% sobre aparições da unidade)"
                )
        else:
            lines.append("  - nenhum")

        lines.append("combinações mais usadas:")
        if row["top_item_combinations"]:
            for combo in row["top_item_combinations"]:
                lines.append(
                    f"  - {combo['uses']}x: " + " + ".join(combo["items"])
                )
        else:
            lines.append("  - nenhuma")

    if errors:
        lines.extend(["", "=" * 140, "ERROS DE LEITURA", "=" * 140])
        lines.extend(errors)

    TXT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        fieldnames = [
            "character_id",
            "display_name",
            "raw_name",
            "rarity_raw_mode",
            "inferred_cost",
            "uses",
            "itemized_uses",
            "itemized_rate",
            "average_items",
            "average_placement",
            "tier_distribution",
            "rarity_distribution",
            "top_items",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    **{k: row[k] for k in fieldnames if k not in {
                        "tier_distribution",
                        "rarity_distribution",
                        "top_items",
                    }},
                    "tier_distribution": json.dumps(
                        row["tier_distribution"], ensure_ascii=False
                    ),
                    "rarity_distribution": json.dumps(
                        row["rarity_distribution"], ensure_ascii=False
                    ),
                    "top_items": " | ".join(
                        f"{item['item_id']} ({item['uses']})"
                        for item in row["top_items"]
                    ),
                }
            )

    JSON_OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "target_set_number": TARGET_SET_NUMBER,
                "target_set_core_name": TARGET_SET_CORE_NAME,
                "cache_json_files": cache_count,
                "set18_matches": matches_count,
                "unique_units": len(rows),
                "read_errors": errors,
                "units": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    matches, errors, cache_count = load_matches()

    if not matches:
        raise RuntimeError("Nenhuma partida do Set 18 foi encontrada no cache.")

    rows = build_rows(collect(matches))

    if not rows:
        raise RuntimeError("Nenhuma unidade foi encontrada nas partidas do Set 18.")

    save_reports(
        rows=rows,
        matches_count=len(matches),
        cache_count=cache_count,
        errors=errors,
    )

    print("=" * 100)
    print("TFT INSIGHT — EXTRAÇÃO DE UNIDADES SET 18 CONCLUÍDA")
    print("=" * 100)
    print(f"Partidas Set 18 : {len(matches)}")
    print(f"Unidades únicas : {len(rows)}")
    print(f"Erros de leitura: {len(errors)}")
    print()
    print(f"TXT : {TXT_OUTPUT}")
    print(f"CSV : {CSV_OUTPUT}")
    print(f"JSON: {JSON_OUTPUT}")


if __name__ == "__main__":
    main()
