from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


# ======================================================================================
# TFT INSIGHT
# ROADMAP 26.7 — INVENTÁRIO REAL DO SET 18
#
# Objetivo:
#
#   - identificar quais partidas pertencem ao TFTSet18;
#   - separar Set 18 de Set 17/outros;
#   - levantar todas as unidades observadas;
#   - levantar todos os itens observados;
#   - contar frequência de aparição;
#   - contar frequência de itemização;
#   - registrar tier/rarity observados;
#   - identificar IDs estranhos/especiais;
#   - NÃO classificar carry/tank/support;
#   - NÃO alterar dados existentes;
#   - NÃO chamar Riot API;
#   - NÃO alterar lógica do produto.
#
# Saídas:
#
#   set18_inventory_report.txt
#   set18_units_inventory.csv
#   set18_items_inventory.csv
#
# Todos os arquivos são relatórios de auditoria.
# ======================================================================================


ROOT = Path(__file__).resolve().parents[1]

RAW_ROOT = ROOT / "data" / "raw"

REPORT_PATH = ROOT / "set18_inventory_report.txt"

UNITS_CSV_PATH = ROOT / "set18_units_inventory.csv"

ITEMS_CSV_PATH = ROOT / "set18_items_inventory.csv"


TARGET_SET = "TFTSet18"


# ======================================================================================
# Helpers
# ======================================================================================


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        if isinstance(payload, dict):
            return payload

        return None

    except Exception:
        return None


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_set_name(value: Any) -> str:
    return str(value or "").strip()


def normalize_id(value: Any) -> str:
    return str(value or "").strip()


def get_match_info(
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    info = payload.get("info")

    if isinstance(info, dict):
        return info

    return None


def get_set_name(
    payload: dict[str, Any],
) -> str:
    info = get_match_info(payload)

    if not info:
        return ""

    candidates = (
        info.get("tft_set_core_name"),
        info.get("tft_set_number"),
        info.get("set_core_name"),
    )

    for value in candidates:
        normalized = normalize_set_name(value)

        if normalized:
            return normalized

    return ""


def is_target_set(
    payload: dict[str, Any],
) -> bool:
    set_name = get_set_name(payload)

    if set_name == TARGET_SET:
        return True

    # Fallback apenas para número explícito.
    info = get_match_info(payload)

    if not info:
        return False

    set_number = info.get("tft_set_number")

    try:
        return int(set_number) == 18
    except (TypeError, ValueError):
        return False


def get_participants(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    info = get_match_info(payload)

    if not info:
        return []

    participants = info.get("participants")

    if not isinstance(participants, list):
        return []

    return [
        participant
        for participant in participants
        if isinstance(participant, dict)
    ]


def get_units(
    participant: dict[str, Any],
) -> list[dict[str, Any]]:
    units = participant.get("units")

    if not isinstance(units, list):
        return []

    return [
        unit
        for unit in units
        if isinstance(unit, dict)
    ]


def get_item_ids(
    unit: dict[str, Any],
) -> list[str]:
    raw_items = (
        unit.get("itemNames")
        or unit.get("items")
        or []
    )

    if not isinstance(raw_items, list):
        return []

    output = []

    for value in raw_items:
        item_id = normalize_id(value)

        if item_id:
            output.append(item_id)

    return output


# ======================================================================================
# Data structures
# ======================================================================================


class UnitStats:
    def __init__(self) -> None:
        self.appearances = 0
        self.itemized_appearances = 0

        self.item_counts = Counter()
        self.tiers = Counter()
        self.rarities = Counter()
        self.names = Counter()

        self.total_items = 0

    def add(
        self,
        *,
        name: str,
        tier: int,
        rarity: int,
        item_ids: list[str],
    ) -> None:
        self.appearances += 1

        if name:
            self.names[name] += 1

        self.tiers[tier] += 1
        self.rarities[rarity] += 1

        item_count = len(item_ids)

        self.item_counts[item_count] += 1
        self.total_items += item_count

        if item_count > 0:
            self.itemized_appearances += 1

    @property
    def most_common_name(self) -> str:
        if not self.names:
            return ""

        return self.names.most_common(1)[0][0]

    @property
    def most_common_tier(self) -> int:
        if not self.tiers:
            return 0

        return self.tiers.most_common(1)[0][0]

    @property
    def most_common_rarity(self) -> int:
        if not self.rarities:
            return 0

        return self.rarities.most_common(1)[0][0]

    @property
    def average_items(self) -> float:
        if self.appearances == 0:
            return 0.0

        return self.total_items / self.appearances

    @property
    def itemized_rate(self) -> float:
        if self.appearances == 0:
            return 0.0

        return (
            self.itemized_appearances
            / self.appearances
            * 100.0
        )


class ItemStats:
    def __init__(self) -> None:
        self.appearances = 0

        self.unit_usage = Counter()
        self.unit_rarities = Counter()
        self.unit_tiers = Counter()

    def add(
        self,
        *,
        character_id: str,
        rarity: int,
        tier: int,
    ) -> None:
        self.appearances += 1

        if character_id:
            self.unit_usage[character_id] += 1

        self.unit_rarities[rarity] += 1
        self.unit_tiers[tier] += 1

    @property
    def unique_units(self) -> int:
        return len(self.unit_usage)

    @property
    def most_used_unit(self) -> str:
        if not self.unit_usage:
            return ""

        return self.unit_usage.most_common(1)[0][0]

    @property
    def most_used_unit_count(self) -> int:
        if not self.unit_usage:
            return 0

        return self.unit_usage.most_common(1)[0][1]


# ======================================================================================
# Inventory
# ======================================================================================


def collect_inventory():
    set_counts = Counter()

    units: dict[str, UnitStats] = defaultdict(UnitStats)
    items: dict[str, ItemStats] = defaultdict(ItemStats)

    total_json = 0
    invalid_json = 0
    target_matches = 0

    target_files: list[Path] = []

    unknown_unit_ids = Counter()
    unusual_item_ids = Counter()

    if not RAW_ROOT.exists():
        raise RuntimeError(
            f"Diretório não encontrado: {RAW_ROOT}"
        )

    for path in RAW_ROOT.rglob("*.json"):
        total_json += 1

        payload = read_json(path)

        if payload is None:
            invalid_json += 1
            continue

        set_name = get_set_name(payload)

        set_counts[
            set_name or "<SEM_SET>"
        ] += 1

        if not is_target_set(payload):
            continue

        target_matches += 1
        target_files.append(path)

        participants = get_participants(payload)

        for participant in participants:
            for unit in get_units(participant):
                character_id = normalize_id(
                    unit.get("character_id")
                )

                name = normalize_id(
                    unit.get("name")
                )

                rarity = safe_int(
                    unit.get("rarity"),
                    0,
                )

                tier = safe_int(
                    unit.get("tier"),
                    1,
                )

                item_ids = get_item_ids(unit)

                if not character_id:
                    unknown_unit_ids[
                        "<EMPTY_CHARACTER_ID>"
                    ] += 1
                    continue

                if not character_id.startswith(
                    "TFT18_"
                ):
                    unknown_unit_ids[
                        character_id
                    ] += 1

                units[character_id].add(
                    name=name,
                    tier=tier,
                    rarity=rarity,
                    item_ids=item_ids,
                )

                for item_id in item_ids:
                    items[item_id].add(
                        character_id=character_id,
                        rarity=rarity,
                        tier=tier,
                    )

                    if not (
                        item_id.startswith("TFT_Item_")
                        or item_id.startswith("TFT18_")
                        or "_Item_" in item_id
                    ):
                        unusual_item_ids[item_id] += 1

    return {
        "total_json": total_json,
        "invalid_json": invalid_json,
        "target_matches": target_matches,
        "set_counts": set_counts,
        "units": units,
        "items": items,
        "target_files": target_files,
        "unknown_unit_ids": unknown_unit_ids,
        "unusual_item_ids": unusual_item_ids,
    }


# ======================================================================================
# CSV
# ======================================================================================


def write_units_csv(
    units: dict[str, UnitStats],
) -> None:
    rows = []

    for character_id, stats in units.items():
        rows.append(
            {
                "character_id": character_id,
                "name": stats.most_common_name,
                "appearances": stats.appearances,
                "itemized_appearances": (
                    stats.itemized_appearances
                ),
                "itemized_rate_pct": (
                    f"{stats.itemized_rate:.2f}"
                ),
                "average_items": (
                    f"{stats.average_items:.3f}"
                ),
                "most_common_tier": (
                    stats.most_common_tier
                ),
                "most_common_rarity": (
                    stats.most_common_rarity
                ),
                "tier_distribution": json.dumps(
                    dict(
                        sorted(
                            stats.tiers.items()
                        )
                    ),
                    ensure_ascii=False,
                ),
                "rarity_distribution": json.dumps(
                    dict(
                        sorted(
                            stats.rarities.items()
                        )
                    ),
                    ensure_ascii=False,
                ),
                "item_count_distribution": json.dumps(
                    dict(
                        sorted(
                            stats.item_counts.items()
                        )
                    ),
                    ensure_ascii=False,
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            -row["appearances"],
            row["character_id"],
        )
    )

    fieldnames = [
        "character_id",
        "name",
        "appearances",
        "itemized_appearances",
        "itemized_rate_pct",
        "average_items",
        "most_common_tier",
        "most_common_rarity",
        "tier_distribution",
        "rarity_distribution",
        "item_count_distribution",
    ]

    with UNITS_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def write_items_csv(
    items: dict[str, ItemStats],
) -> None:
    rows = []

    for item_id, stats in items.items():
        top_units = stats.unit_usage.most_common(10)

        rows.append(
            {
                "item_id": item_id,
                "appearances": stats.appearances,
                "unique_units": stats.unique_units,
                "most_used_unit": (
                    stats.most_used_unit
                ),
                "most_used_unit_count": (
                    stats.most_used_unit_count
                ),
                "top_units": json.dumps(
                    top_units,
                    ensure_ascii=False,
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            -row["appearances"],
            row["item_id"],
        )
    )

    fieldnames = [
        "item_id",
        "appearances",
        "unique_units",
        "most_used_unit",
        "most_used_unit_count",
        "top_units",
    ]

    with ITEMS_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ======================================================================================
# TXT report
# ======================================================================================


def write_report(result: dict[str, Any]) -> None:
    set_counts: Counter = result["set_counts"]
    units: dict[str, UnitStats] = result["units"]
    items: dict[str, ItemStats] = result["items"]

    unknown_unit_ids: Counter = (
        result["unknown_unit_ids"]
    )

    unusual_item_ids: Counter = (
        result["unusual_item_ids"]
    )

    lines: list[str] = []

    def write(value: str = "") -> None:
        lines.append(value)

    def section(title: str) -> None:
        write()
        write("=" * 120)
        write(title)
        write("=" * 120)

    section(
        "TFT INSIGHT — ROADMAP 26.7 — "
        "INVENTÁRIO REAL DO TFT SET 18"
    )

    write(f"Target set             : {TARGET_SET}")
    write(
        f"JSONs examinados       : "
        f"{result['total_json']}"
    )
    write(
        f"JSONs inválidos        : "
        f"{result['invalid_json']}"
    )
    write(
        f"Partidas Set 18        : "
        f"{result['target_matches']}"
    )
    write(
        f"Unidades únicas        : "
        f"{len(units)}"
    )
    write(
        f"Itens únicos           : "
        f"{len(items)}"
    )

    section("1. DISTRIBUIÇÃO DE PARTIDAS POR SET")

    for set_name, count in set_counts.most_common():
        write(
            f"{set_name:<40} {count:>8}"
        )

    section("2. UNIDADES OBSERVADAS NO SET 18")

    write(
        f"{'CHARACTER_ID':<42}"
        f"{'APARIÇÕES':>12}"
        f"{'ITEMIZADA %':>14}"
        f"{'AVG ITENS':>12}"
        f"{'TIER':>8}"
        f"{'RARITY':>10}"
    )

    write("-" * 120)

    sorted_units = sorted(
        units.items(),
        key=lambda pair: (
            -pair[1].appearances,
            pair[0],
        ),
    )

    for character_id, stats in sorted_units:
        write(
            f"{character_id:<42}"
            f"{stats.appearances:>12}"
            f"{stats.itemized_rate:>13.1f}%"
            f"{stats.average_items:>12.2f}"
            f"{stats.most_common_tier:>8}"
            f"{stats.most_common_rarity:>10}"
        )

    section(
        "3. UNIDADES MAIS FREQUENTEMENTE ITEMIZADAS"
    )

    sorted_itemized_units = sorted(
        units.items(),
        key=lambda pair: (
            -pair[1].itemized_rate,
            -pair[1].appearances,
            pair[0],
        ),
    )

    for character_id, stats in sorted_itemized_units[:100]:
        write(
            f"{character_id:<42}"
            f"appearances={stats.appearances:<6} "
            f"itemized={stats.itemized_rate:>6.1f}% "
            f"avg_items={stats.average_items:.2f}"
        )

    section("4. ITENS OBSERVADOS NO SET 18")

    write(
        f"{'ITEM_ID':<65}"
        f"{'USOS':>10}"
        f"{'UNIDADES':>12}"
    )

    write("-" * 100)

    sorted_items = sorted(
        items.items(),
        key=lambda pair: (
            -pair[1].appearances,
            pair[0],
        ),
    )

    for item_id, stats in sorted_items:
        write(
            f"{item_id:<65}"
            f"{stats.appearances:>10}"
            f"{stats.unique_units:>12}"
        )

    section("5. TOP UNIDADES POR ITEM")

    for item_id, stats in sorted_items[:100]:
        top = ", ".join(
            f"{unit}={count}"
            for unit, count
            in stats.unit_usage.most_common(8)
        )

        write()
        write(
            f"{item_id} — usos={stats.appearances}"
        )
        write(
            f"  {top or '-'}"
        )

    section(
        "6. CHARACTER_IDS QUE NÃO COMEÇAM COM TFT18_"
    )

    if not unknown_unit_ids:
        write(
            "Nenhum character_id fora do padrão TFT18_ "
            "foi encontrado."
        )
    else:
        for character_id, count in (
            unknown_unit_ids.most_common()
        ):
            write(
                f"{character_id:<70} {count}"
            )

    section(
        "7. ITEM_IDS COM FORMATO INCOMUM"
    )

    if not unusual_item_ids:
        write(
            "Nenhum item_id com formato incomum encontrado."
        )
    else:
        for item_id, count in (
            unusual_item_ids.most_common()
        ):
            write(
                f"{item_id:<80} {count}"
            )

    section("8. ARQUIVOS GERADOS")

    write(relative_path(REPORT_PATH))
    write(relative_path(UNITS_CSV_PATH))
    write(relative_path(ITEMS_CSV_PATH))

    section("9. PRÓXIMA ETAPA")

    write(
        "Este inventário NÃO classifica unidades nem itens."
    )

    write()
    write(
        "A próxima etapa será cruzar os IDs encontrados "
        "com os dados estáticos PT-BR para produzir:"
    )

    write()
    write(
        "  character_id -> nome oficial"
    )
    write(
        "  item_id      -> nome oficial"
    )

    write()
    write(
        "Somente depois começará a classificação manual."
    )

    write()
    write(
        "Casos ambíguos deverão ser separados para "
        "revisão humana em vez de classificados por suposição."
    )

    REPORT_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except Exception:
        return str(path)


# ======================================================================================
# Main
# ======================================================================================


def main() -> int:
    try:
        result = collect_inventory()

    except Exception as error:
        print()
        print("ERRO NA AUDITORIA")
        print(error)
        print()

        return 1

    write_units_csv(
        result["units"]
    )

    write_items_csv(
        result["items"]
    )

    write_report(result)

    print("=" * 90)
    print(
        "TFT INSIGHT — ROADMAP 26.7 — SET 18 INVENTORY"
    )
    print("=" * 90)
    print()
    print(
        f"JSONs examinados : "
        f"{result['total_json']}"
    )
    print(
        f"Partidas Set 18  : "
        f"{result['target_matches']}"
    )
    print(
        f"Unidades únicas  : "
        f"{len(result['units'])}"
    )
    print(
        f"Itens únicos     : "
        f"{len(result['items'])}"
    )
    print()
    print("Arquivos gerados:")
    print(REPORT_PATH)
    print(UNITS_CSV_PATH)
    print(ITEMS_CSV_PATH)
    print()
    print(
        "Nenhuma classificação de role foi criada."
    )
    print("=" * 90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())