"""
Gerenciamento das configurações da aplicação.
"""

import os

from dotenv import load_dotenv

from src.constants import DEFAULT_MATCH_COUNT

load_dotenv()


class Config:
    """
    Configurações carregadas a partir do arquivo .env.
    """

    RIOT_API_KEY: str | None = os.getenv("RIOT_API_KEY")

    PLAYER_GAME_NAME: str | None = os.getenv("PLAYER_GAME_NAME")
    PLAYER_TAG_LINE: str | None = os.getenv("PLAYER_TAG_LINE")

    MASTER_GAME_NAME: str | None = os.getenv("MASTER_GAME_NAME")
    MASTER_TAG_LINE: str | None = os.getenv("MASTER_TAG_LINE")

    MATCH_COUNT: int = int(
        os.getenv(
            "MATCH_COUNT",
            str(DEFAULT_MATCH_COUNT)
        )
    )

    PLAYERS = [
        {
            "game_name": PLAYER_GAME_NAME,
            "tag_line": PLAYER_TAG_LINE,
        },
        {
            "game_name": MASTER_GAME_NAME,
            "tag_line": MASTER_TAG_LINE,
        },
    ]

    @classmethod
    def validate(cls) -> None:
        """
        Valida se todas as variáveis obrigatórias foram carregadas.
        """

        required_variables = {
            "RIOT_API_KEY": cls.RIOT_API_KEY,
            "PLAYER_GAME_NAME": cls.PLAYER_GAME_NAME,
            "PLAYER_TAG_LINE": cls.PLAYER_TAG_LINE,
            "MASTER_GAME_NAME": cls.MASTER_GAME_NAME,
            "MASTER_TAG_LINE": cls.MASTER_TAG_LINE,
        }

        missing = [
            key
            for key, value in required_variables.items()
            if not value
        ]

        if missing:
            raise ValueError(
                "As seguintes variáveis não foram encontradas no .env:\n"
                + "\n".join(f"- {item}" for item in missing)
            )