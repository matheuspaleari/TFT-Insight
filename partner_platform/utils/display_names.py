from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path


_TFT_SET_PREFIX_RE = re.compile(
    r"^TFT\d+_",
    flags=re.IGNORECASE,
)

_DA_SET_PREFIX_RE = re.compile(
    r"^DA[ _-]*\d+[ _-]*",
    flags=re.IGNORECASE,
)

_DA_PREFIX_RE = re.compile(
    r"^DA[ _-]+",
    flags=re.IGNORECASE,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_UNIT_CATALOG_PATH = (
    _PROJECT_ROOT
    / "data"
    / "role_inference"
    / "set18"
    / "unit_catalog_v2.json"
)

_ITEM_CATALOG_PATH = (
    _PROJECT_ROOT
    / "data"
    / "role_inference"
    / "set18"
    / "item_catalog_v2.json"
)



def _split_camel_case(
    value: str,
) -> str:
    return re.sub(
        r"(?<=[a-z])(?=[A-Z])",
        " ",
        value,
    )


def _compact_spaces(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


@lru_cache(maxsize=1)
def _unit_display_names() -> dict[str, str]:
    names: dict[str, str] = {}

    try:
        payload = json.loads(
            _UNIT_CATALOG_PATH.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return names

    entries = payload.get("units", [])
    if not isinstance(entries, list):
        return names

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        character_id = str(
            entry.get("character_id", "")
        ).strip()
        display_name = str(
            entry.get("display_name", "")
        ).strip()

        if character_id and display_name:
            names[character_id] = display_name

    return names


@lru_cache(maxsize=1)
def _item_display_names() -> dict[str, str]:
    names: dict[str, str] = {}

    try:
        payload = json.loads(
            _ITEM_CATALOG_PATH.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return names

    entries = payload.get("items", [])
    if not isinstance(entries, list):
        return names

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        item_id = str(
            entry.get("riot_item_id", "")
        ).strip()
        display_name = str(
            entry.get("display_name", "")
        ).strip()

        if item_id and display_name:
            names[item_id] = display_name

    return names


def friendly_game_name(
    value: str | None,
    *,
    empty: str = "-",
) -> str:
    """
    Retorna primeiro o nome público do catálogo manual Set 18.

    Para IDs que não pertencem ao catálogo, preserva o comportamento legado
    de sanitização para impedir que identificadores técnicos apareçam na UI.
    """
    raw = str(
        value
        or ""
    ).strip()

    if not raw:
        return empty

    catalog_name = _unit_display_names().get(raw)
    if catalog_name:
        return catalog_name

    text = raw

    had_da_prefix = bool(
        _DA_SET_PREFIX_RE.match(
            text
        )
        or _DA_PREFIX_RE.match(
            text
        )
    )

    text = _TFT_SET_PREFIX_RE.sub(
        "",
        text,
        count=1,
    )

    text = re.sub(
        r"^TFT_",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    text = _DA_SET_PREFIX_RE.sub(
        "",
        text,
        count=1,
    )

    text = _DA_PREFIX_RE.sub(
        "",
        text,
        count=1,
    )

    text = text.replace(
        "_",
        " ",
    )

    text = _split_camel_case(
        text
    )

    if had_da_prefix:
        text = re.sub(
            r"(?<=[A-Za-z])\d+$",
            "",
            text,
        )

    text = _compact_spaces(
        text
    )

    return text or empty


def friendly_item_name(
    value: str | None,
    *,
    empty: str = "-",
) -> str:
    """
    Retorna primeiro o nome PT-BR validado do catálogo manual Set 18.

    O fallback legado existe apenas para IDs ausentes do catálogo e não cria
    tradução nem classificação.
    """
    raw = str(
        value
        or ""
    ).strip()

    if not raw:
        return empty

    catalog_name = _item_display_names().get(raw)
    if catalog_name:
        return catalog_name

    text = raw

    text = _TFT_SET_PREFIX_RE.sub(
        "",
        text,
        count=1,
    )

    text = re.sub(
        r"^TFT_",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    text = _DA_SET_PREFIX_RE.sub(
        "",
        text,
        count=1,
    )

    text = _DA_PREFIX_RE.sub(
        "",
        text,
        count=1,
    )

    for prefix in (
        "Item_Artifact_",
        "Item_Radiant_",
        "Item_",
    ):
        if text.startswith(
            prefix
        ):
            text = text[
                len(prefix):
            ]
            break

    text = text.replace(
        "_",
        " ",
    )

    text = _split_camel_case(
        text
    )

    for prefix in (
        "TFT ",
        "Mod ",
    ):
        if text.startswith(
            prefix
        ):
            text = text[
                len(prefix):
            ]
            break

    text = _compact_spaces(
        text
    )

    return text or empty


_TECHNICAL_GAME_ID_IN_TEXT_RE = re.compile(
    r"""
    (?<![A-Za-z0-9])
    (?:
        TFT\d+_[A-Za-z0-9_]+
        |
        DA[ _-]*\d+[ _-]*[A-Za-z][A-Za-z0-9_-]*
        |
        DA[ _-]+[A-Za-z][A-Za-z0-9_-]*
        (?:[ _-][A-Za-z][A-Za-z0-9_-]*)*
        \d+
    )
    """,
    flags=re.VERBOSE,
)


def friendly_public_text(
    value: str | None,
    *,
    empty: str = "",
) -> str:
    """
    Sanitiza texto público que pode conter IDs técnicos embutidos em frases.

    IDs de unidade encontrados no texto passam pela mesma autoridade de
    display do catálogo Set 18 antes do fallback de sanitização.
    """
    text = str(
        value
        or ""
    )

    if not text:
        return empty

    def _replace(
        match: re.Match[str],
    ) -> str:
        return friendly_game_name(
            match.group(0),
            empty="",
        )

    return _TECHNICAL_GAME_ID_IN_TEXT_RE.sub(
        _replace,
        text,
    )
