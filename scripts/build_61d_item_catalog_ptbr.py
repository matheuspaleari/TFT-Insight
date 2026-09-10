from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
import urllib.request
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STATE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "challenger"
)

INPUT_CSV_PATH = (
    STATE_DIRECTORY
    / "audit_61c_observed_items.csv"
)

PTBR_CACHE_PATH = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "set18"
    / "communitydragon_pt_br_latest.json"
)

OUTPUT_JSON_PATH = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "set18"
    / "item_catalog_v1_review.json"
)

OUTPUT_CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "set18"
    / "item_catalog_v1_review.csv"
)

COMMUNITYDRAGON_PTBR_URL = (
    "https://raw.communitydragon.org/latest/cdragon/tft/pt_br.json"
)


@dataclass(frozen=True)
class Candidate:
    api_name: str
    display_name: str
    score: int
    method: str
    raw: dict[str, Any]


def normalize(value: str) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value or "").casefold(),
    )


def strip_namespace(value: str) -> str:
    text = normalize(value)

    prefixes = (
        "tft18item",
        "tftitem",
        "tft18",
        "tft",
        "daartifact",
        "daradiant",
        "dasupport",
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


def read_input_rows() -> list[dict[str, str]]:
    if not INPUT_CSV_PATH.exists():
        raise RuntimeError(
            f"CSV da #61C não encontrado: {INPUT_CSV_PATH}"
        )

    with INPUT_CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fh:
        return list(csv.DictReader(fh))


def download_ptbr_catalog(refresh: bool) -> dict[str, Any]:
    PTBR_CACHE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PTBR_CACHE_PATH.exists() and not refresh:
        return json.loads(
            PTBR_CACHE_PATH.read_text(
                encoding="utf-8"
            )
        )

    print(
        "Baixando CommunityDragon PT-BR atual..."
    )

    request = urllib.request.Request(
        COMMUNITYDRAGON_PTBR_URL,
        headers={
            "User-Agent": (
                "TFT-Insight/61D "
                "(item catalog bootstrap)"
            )
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=90,
    ) as response:
        payload = response.read()

    PTBR_CACHE_PATH.write_bytes(payload)

    return json.loads(
        payload.decode("utf-8")
    )


def collect_item_like_dicts(
    node: Any,
    output: list[dict[str, Any]],
) -> None:
    if isinstance(node, dict):
        api_name = node.get("apiName")
        name = node.get("name")

        if (
            isinstance(api_name, str)
            and api_name.strip()
            and isinstance(name, str)
            and name.strip()
        ):
            output.append(node)

        for value in node.values():
            collect_item_like_dicts(
                value,
                output,
            )

    elif isinstance(node, list):
        for value in node:
            collect_item_like_dicts(
                value,
                output,
            )


def unique_item_records(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    collect_item_like_dicts(
        payload,
        collected,
    )

    result: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for item in collected:
        api_name = str(
            item.get("apiName", "")
        ).strip()
        name = str(
            item.get("name", "")
        ).strip()

        key = (
            api_name.casefold(),
            name.casefold(),
        )

        if key not in result:
            result[key] = item

    return list(result.values())


def build_indices(
    items: list[dict[str, Any]],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    exact: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    stripped: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for item in items:
        api_name = str(
            item.get("apiName", "")
        ).strip()

        exact.setdefault(
            normalize(api_name),
            [],
        ).append(item)

        stripped.setdefault(
            strip_namespace(api_name),
            [],
        ).append(item)

    return exact, stripped


def item_type_candidate(
    api_name: str,
    raw: dict[str, Any],
) -> str:
    """
    Apenas um candidato estrutural.
    A classificação manual continua sendo a autoridade.
    """
    text = (
        f"{api_name} "
        f"{raw.get('name', '')}"
    ).casefold()

    composition = raw.get("composition")

    if (
        "emblem" in text
        or "spatula" in text
        or "trait" in text
    ):
        return "emblem_or_trait"

    if (
        "radiant" in text
        or "masterwork" in text
    ):
        return "radiant"

    if (
        "artifact" in text
        or "ornn" in text
    ):
        return "artifact"

    if "support" in text:
        return "support_item"

    if isinstance(composition, list):
        if len(composition) >= 2:
            return "completed"
        if len(composition) == 1:
            return "component_or_special"

    return "review"


def score_candidates(
    riot_id: str,
    row: dict[str, str],
    exact_index: dict[
        str,
        list[dict[str, Any]],
    ],
    stripped_index: dict[
        str,
        list[dict[str, Any]],
    ],
) -> list[Candidate]:
    candidates: dict[
        tuple[str, str],
        Candidate,
    ] = {}

    def add(
        item: dict[str, Any],
        score: int,
        method: str,
    ) -> None:
        api_name = str(
            item.get("apiName", "")
        ).strip()

        display_name = str(
            item.get("name", "")
        ).strip()

        key = (
            api_name.casefold(),
            display_name.casefold(),
        )

        old = candidates.get(key)

        candidate = Candidate(
            api_name=api_name,
            display_name=display_name,
            score=score,
            method=method,
            raw=item,
        )

        if old is None or score > old.score:
            candidates[key] = candidate

    # 1) Candidato já descoberto pela #61C.
    prior_id = str(
        row.get(
            "normalized_candidate_id",
            "",
        )
        or ""
    ).strip()

    if prior_id:
        for item in exact_index.get(
            normalize(prior_id),
            [],
        ):
            add(
                item,
                100,
                "61c_candidate",
            )

    # 2) Alias DA_* -> TFT_Item_*.
    if riot_id.startswith("DA_"):
        suffix = riot_id[3:]

        aliases = (
            f"TFT_Item_{suffix}",
            f"TFT18_Item_{suffix}",
            suffix,
        )

        for alias in aliases:
            for item in exact_index.get(
                normalize(alias),
                [],
            ):
                add(
                    item,
                    95,
                    "namespace_alias",
                )

    # 3) apiName normalizado exato.
    for item in exact_index.get(
        normalize(riot_id),
        [],
    ):
        add(
            item,
            100,
            "exact_api_name",
        )

    # 4) Mesmo sufixo após remover namespaces.
    stripped = strip_namespace(riot_id)

    for item in stripped_index.get(
        stripped,
        [],
    ):
        add(
            item,
            90,
            "normalized_suffix",
        )

    result = sorted(
        candidates.values(),
        key=lambda item: (
            -item.score,
            item.api_name.casefold(),
            item.display_name.casefold(),
        ),
    )

    return result


def safe_int(value: Any) -> int:
    try:
        return int(
            float(
                str(value or "0")
            )
        )
    except (TypeError, ValueError):
        return 0


def main() -> None:
    refresh = (
        "--refresh-ptbr"
        in sys.argv[1:]
    )

    print("=" * 112)
    print(
        "TFT INSIGHT — #61D ITEM CATALOG PT-BR / MANUAL REVIEW"
    )
    print("=" * 112)

    rows = read_input_rows()

    ptbr_payload = download_ptbr_catalog(
        refresh=refresh,
    )

    rich_items = unique_item_records(
        ptbr_payload
    )

    exact_index, stripped_index = (
        build_indices(
            rich_items
        )
    )

    output: list[dict[str, Any]] = []

    resolved = 0
    ambiguous = 0
    unresolved = 0

    for row in rows:
        riot_id = str(
            row.get(
                "riot_item_id",
                "",
            )
            or ""
        ).strip()

        if not riot_id:
            continue

        candidates = score_candidates(
            riot_id=riot_id,
            row=row,
            exact_index=exact_index,
            stripped_index=stripped_index,
        )

        best = (
            candidates[0]
            if candidates
            else None
        )

        same_top_score = (
            [
                item
                for item in candidates
                if (
                    best is not None
                    and item.score == best.score
                )
            ]
            if best is not None
            else []
        )

        if best is None:
            status = "unresolved"
            unresolved += 1
        elif len(same_top_score) > 1:
            status = "ambiguous"
            ambiguous += 1
        else:
            status = "resolved_candidate"
            resolved += 1

        output.append(
            {
                "riot_item_id": riot_id,
                "display_name_ptbr": (
                    best.display_name
                    if best is not None
                    else ""
                ),
                "communitydragon_api_name": (
                    best.api_name
                    if best is not None
                    else ""
                ),
                "resolution_status": status,
                "resolution_method": (
                    best.method
                    if best is not None
                    else ""
                ),
                "resolution_score": (
                    best.score
                    if best is not None
                    else 0
                ),
                "candidate_count": len(
                    candidates
                ),
                "item_type_candidate": (
                    item_type_candidate(
                        best.api_name,
                        best.raw,
                    )
                    if best is not None
                    else "review"
                ),
                "observed_uses": safe_int(
                    row.get(
                        "observed_uses"
                    )
                ),
                "carry_uses": safe_int(
                    row.get(
                        "carry_uses"
                    )
                ),
                "tank_uses": safe_int(
                    row.get(
                        "tank_uses"
                    )
                ),
                "support_uses": safe_int(
                    row.get(
                        "support_uses"
                    )
                ),

                # Campos que vamos preencher/confirmar manualmente.
                "manual_category": "",
                "manual_role_label": "",
                "carry_weight": "",
                "tank_weight": "",
                "support_weight": "",
                "learning_enabled": "",
                "confirmed": False,
                "notes": "",
            }
        )

    output.sort(
        key=lambda item: (
            -item["observed_uses"],
            item["riot_item_id"],
        )
    )

    OUTPUT_JSON_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalog = {
        "schema_version": "1.0-review",
        "set": {
            "number": 18,
            "core_name": "TFTSet18",
        },
        "source": {
            "observations": str(
                INPUT_CSV_PATH
            ),
            "ptbr": (
                COMMUNITYDRAGON_PTBR_URL
            ),
        },
        "policy": {
            "manual_classification_is_authority": True,
            "automatic_type_is_candidate_only": True,
            "never_use_unconfirmed_item_as_manual_truth": True,
        },
        "items": output,
    }

    OUTPUT_JSON_PATH.write_text(
        json.dumps(
            catalog,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    fieldnames = [
        "riot_item_id",
        "display_name_ptbr",
        "communitydragon_api_name",
        "resolution_status",
        "resolution_method",
        "resolution_score",
        "candidate_count",
        "item_type_candidate",
        "observed_uses",
        "carry_uses",
        "tank_uses",
        "support_uses",
        "manual_category",
        "manual_role_label",
        "carry_weight",
        "tank_weight",
        "support_weight",
        "learning_enabled",
        "confirmed",
        "notes",
    ]

    with OUTPUT_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(output)

    print(
        f"Itens da #61C                : {len(rows)}"
    )
    print(
        f"Registros PT-BR inspecionados: {len(rich_items)}"
    )
    print()
    print(
        f"Resolvidos como candidato    : {resolved}"
    )
    print(
        f"Ambíguos                     : {ambiguous}"
    )
    print(
        f"Sem candidato                : {unresolved}"
    )

    print()
    print("-" * 112)
    print("TOP 30 PARA REVISÃO MANUAL")
    print("-" * 112)
    print(
        f"{'ID RIOT':<42} "
        f"{'USOS':>6} "
        f"{'CARRY':>7} "
        f"{'TANK':>7} "
        f"{'SUP':>6} "
        f"{'STATUS':<19} "
        f"NOME PT-BR"
    )

    for item in output[:30]:
        print(
            f"{item['riot_item_id'][:41]:<42} "
            f"{item['observed_uses']:>6} "
            f"{item['carry_uses']:>7} "
            f"{item['tank_uses']:>7} "
            f"{item['support_uses']:>6} "
            f"{item['resolution_status'][:18]:<19} "
            f"{(item['display_name_ptbr'] or '-')[:45]}"
        )

    print()
    print(
        f"JSON de revisão : {OUTPUT_JSON_PATH}"
    )
    print(
        f"CSV de revisão  : {OUTPUT_CSV_PATH}"
    )

    if unresolved:
        print()
        print(
            "IMPORTANTE: itens sem candidato NÃO receberam nome inventado."
        )

    print()
    print(
        "Próximo passo: envie o CSV/JSON gerado para fazermos "
        "a classificação manual por lotes."
    )


if __name__ == "__main__":
    main()
