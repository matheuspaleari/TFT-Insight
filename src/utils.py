"""
Funções utilitárias do projeto.
"""

import json
from pathlib import Path
from typing import Any


def ensure_directory(directory: str | Path) -> None:
    """
    Cria um diretório caso ele ainda não exista.
    """

    Path(directory).mkdir(
        parents=True,
        exist_ok=True
    )


def save_json(
    data: dict[str, Any],
    filepath: str | Path
) -> None:
    """
    Salva um dicionário em um arquivo JSON.
    """

    path = Path(filepath)

    with path.open(
        mode="w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )