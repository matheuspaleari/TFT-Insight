from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


KEYWORDS_OF_INTEREST = (
    "gold",
    "economy",
    "income",
    "streak",
    "xp",
    "level",
    "round",
    "stage",
    "damage",
    "health",
    "placement",
    "rank",
    "standing",
    "augment",
    "bench",
    "shop",
    "roll",
    "item",
    "trait",
    "board",
)


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def walk_schema(value: Any, path: str, schema: dict[str, set[str]]) -> None:
    schema.setdefault(path, set()).add(type_name(value))

    if isinstance(value, dict):
        for key, child in value.items():
            walk_schema(child, f"{path}.{key}", schema)
    elif isinstance(value, list):
        for child in value:
            walk_schema(child, f"{path}[]", schema)


def flatten_leaf_examples(
    value: Any,
    path: str,
    examples: dict[str, list[Any]],
    max_examples: int = 5,
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            flatten_leaf_examples(
                child,
                f"{path}.{key}",
                examples,
                max_examples,
            )
        return

    if isinstance(value, list):
        if not value:
            examples.setdefault(f"{path}[]", [])
            return

        for child in value:
            flatten_leaf_examples(
                child,
                f"{path}[]",
                examples,
                max_examples,
            )
        return

    bucket = examples.setdefault(path, [])
    if value not in bucket and len(bucket) < max_examples:
        bucket.append(value)


def load_eog_payload(path: Path) -> dict[str, Any]:
    root = json.loads(path.read_text(encoding="utf-8"))

    try:
        eog = root["results"]["tft_eog_stats"]["data"]
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            "Arquivo nao possui results.tft_eog_stats.data."
        ) from exc

    if not isinstance(eog, dict):
        raise SystemExit("tft_eog_stats.data nao e um objeto JSON.")

    return eog


def summarize_board(player: dict[str, Any]) -> dict[str, Any]:
    pieces = player.get("boardPieces") or []

    units = []
    all_items = []
    all_traits = []

    for piece in pieces:
        if not isinstance(piece, dict):
            continue

        items = [
            item.get("name")
            for item in piece.get("items", [])
            if isinstance(item, dict)
        ]

        traits = [
            trait.get("name")
            for trait in piece.get("traits", [])
            if isinstance(trait, dict)
        ]

        units.append(
            {
                "name": piece.get("name"),
                "championId": piece.get("championId"),
                "level": piece.get("level"),
                "price": piece.get("price"),
                "items": items,
                "traits": traits,
            }
        )

        all_items.extend(x for x in items if x)
        all_traits.extend(x for x in traits if x)

    return {
        "unit_count": len(units),
        "units": units,
        "item_count": len(all_items),
        "items": all_items,
        "traits": dict(Counter(all_traits)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Disseca um JSON de whitelist probe contendo "
            "tft-eog-stats e gera inventario de schema."
        )
    )
    parser.add_argument(
        "input",
        help="Arquivo whitelist_probe_post_game_*.json",
    )
    parser.add_argument(
        "--output",
        default="data/eog_schema_analysis",
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        raise SystemExit(f"Arquivo nao encontrado: {input_path}")

    eog = load_eog_payload(input_path)

    schema: dict[str, set[str]] = {}
    examples: dict[str, list[Any]] = {}

    walk_schema(eog, "$", schema)
    flatten_leaf_examples(eog, "$", examples)

    local_player = eog.get("localPlayer") or {}
    players = eog.get("players") or []

    player_summaries = []
    for player in players:
        if not isinstance(player, dict):
            continue

        player_summaries.append(
            {
                "riot_id": (
                    f"{player.get('riotIdGameName', '')}"
                    f"#{player.get('riotIdTagLine', '')}"
                ),
                "rank": player.get("rank"),
                "ffaStanding": player.get("ffaStanding"),
                "health": player.get("health"),
                "isLocalPlayer": player.get("isLocalPlayer"),
                "board": summarize_board(player),
                "augments": player.get("augments"),
                "setCoreName": player.get("setCoreName"),
            }
        )

    interesting_paths = []
    for path in sorted(schema):
        lower = path.lower()
        if any(keyword in lower for keyword in KEYWORDS_OF_INTEREST):
            interesting_paths.append(path)

    report = {
        "source_file": str(input_path),
        "top_level_keys": sorted(eog.keys()),
        "summary": {
            "gameId": eog.get("gameId"),
            "gameLength": eog.get("gameLength"),
            "isRanked": eog.get("isRanked"),
            "queueId": eog.get("queueId"),
            "queueType": eog.get("queueType"),
            "players_count": len(players),
            "schema_paths": len(schema),
            "local_rank": local_player.get("rank"),
            "local_ffaStanding": local_player.get("ffaStanding"),
            "local_health": local_player.get("health"),
            "local_board_units": len(local_player.get("boardPieces") or []),
            "local_augments_count": len(local_player.get("augments") or []),
        },
        "local_player": {
            "riot_id": (
                f"{local_player.get('riotIdGameName', '')}"
                f"#{local_player.get('riotIdTagLine', '')}"
            ),
            "rank": local_player.get("rank"),
            "ffaStanding": local_player.get("ffaStanding"),
            "health": local_player.get("health"),
            "board": summarize_board(local_player),
            "augments": local_player.get("augments"),
            "customAugmentContainer": local_player.get(
                "customAugmentContainer"
            ),
            "companion": local_player.get("companion"),
        },
        "players": player_summaries,
        "schema": {
            path: sorted(types)
            for path, types in sorted(schema.items())
        },
        "examples": examples,
        "interesting_paths": interesting_paths,
        "missing_interest_terms": {
            term: not any(
                term in path.lower()
                for path in schema
            )
            for term in (
                "gold",
                "economy",
                "income",
                "xp",
                "round",
                "stage",
                "damage",
                "bench",
                "shop",
                "roll",
            )
        },
    }

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem
    json_out = outdir / f"{stem}_schema_report.json"
    txt_out = outdir / f"{stem}_schema_report.txt"

    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "TFT INSIGHT / ROADMAP 25.0G - EOG SCHEMA ANALYZER",
        "=" * 110,
        f"Fonte: {input_path}",
        "",
        "RESUMO",
        "-" * 110,
        f"gameId             : {report['summary']['gameId']}",
        f"gameLength         : {report['summary']['gameLength']}",
        f"isRanked           : {report['summary']['isRanked']}",
        f"queueId            : {report['summary']['queueId']}",
        f"queueType          : {report['summary']['queueType']}",
        f"players_count      : {report['summary']['players_count']}",
        f"schema_paths       : {report['summary']['schema_paths']}",
        f"local_rank         : {report['summary']['local_rank']}",
        f"local_ffaStanding  : {report['summary']['local_ffaStanding']}",
        f"local_health       : {report['summary']['local_health']}",
        f"local_board_units  : {report['summary']['local_board_units']}",
        f"local_augments     : {report['summary']['local_augments_count']}",
        "",
        "TOP-LEVEL KEYS",
        "-" * 110,
        *report["top_level_keys"],
        "",
        "JOGADOR LOCAL - BOARD FINAL",
        "-" * 110,
    ]

    for unit in report["local_player"]["board"]["units"]:
        items = ", ".join(unit["items"]) if unit["items"] else "-"
        traits = ", ".join(unit["traits"]) if unit["traits"] else "-"
        lines.append(
            f"{unit['name']} | estrela/level={unit['level']} | "
            f"custo={unit['price']} | itens=[{items}] | traits=[{traits}]"
        )

    lines.extend([
        "",
        "CLASSIFICACAO DOS 8 JOGADORES",
        "-" * 110,
    ])

    for player in sorted(
        player_summaries,
        key=lambda x: (
            x["rank"] is None,
            x["rank"] if x["rank"] is not None else 999,
        ),
    ):
        lines.append(
            f"{player['rank']}o | {player['riot_id']} | "
            f"board={player['board']['unit_count']} | "
            f"health={player['health']} | "
            f"local={player['isLocalPlayer']}"
        )

    lines.extend([
        "",
        "CAMINHOS DE SCHEMA",
        "-" * 110,
    ])

    for path, types in report["schema"].items():
        lines.append(f"{path} :: {', '.join(types)}")

    lines.extend([
        "",
        "TERMOS IMPORTANTES AUSENTES NO SCHEMA",
        "-" * 110,
    ])

    for term, missing in report["missing_interest_terms"].items():
        lines.append(
            f"{term:<12} {'AUSENTE' if missing else 'ENCONTRADO'}"
        )

    txt_out.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 110)
    print("TFT INSIGHT / ROADMAP 25.0G - EOG SCHEMA ANALYZER")
    print("=" * 110)
    print(f"Schema paths : {len(schema)}")
    print(f"Players      : {len(players)}")
    print(f"Local rank   : {local_player.get('rank')}")
    print(f"Local board  : {len(local_player.get('boardPieces') or [])} unidades")
    print()
    print(f"JSON: {json_out}")
    print(f"TXT : {txt_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
