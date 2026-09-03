from __future__ import annotations

import re


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


def friendly_game_name(
    value: str | None,
    *,
    empty: str = "-",
) -> str:
    """
    Normaliza nomes de campeões, unidades e traits apenas para apresentação.

    Exemplos:
    TFT18_Zyra -> Zyra
    DA 18 Zyra -> Zyra
    DA18_Zyra -> Zyra
    DA_18_Zyra -> Zyra
    DA Flora Fatalis18 -> Flora Fatalis
    """
    text = str(
        value
        or ""
    ).strip()

    if not text:
        return empty

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
    Normaliza IDs técnicos de itens sem misturar regras de item com unidades.
    """
    text = str(
        value
        or ""
    ).strip()

    if not text:
        return empty

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

    Importante:
    - o regex é case-sensitive de propósito;
    - isso evita interpretar palavras normais em português como "da"
      como se fossem o prefixo técnico "DA".

    Exemplos:
        "o carry foi DA_18_Morgana"
        -> "o carry foi Morgana"

        "linha centrada em TFT18_Zyra"
        -> "linha centrada em Zyra"
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
