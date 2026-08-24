"""
Funções auxiliares para identificação de patches do TFT.
"""

import re
from typing import Any


def extract_patch(match_data: dict[str, Any]) -> str | None:
    """
    Extrai o patch principal de uma partida.

    Exemplo:
        "Version 16.15.607.1234" -> "16.15"
    """

    info = match_data.get("info")

    if not isinstance(info, dict):
        return None

    game_version = info.get("game_version")

    if not isinstance(game_version, str):
        return None

    match = re.search(r"(\d+\.\d+)", game_version)

    if match is None:
        return None

    return match.group(1)