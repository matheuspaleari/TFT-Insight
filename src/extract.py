"""
Camada responsável pela extração de dados da Riot API.
"""

from __future__ import annotations

import re
import time
import unicodedata
from pathlib import Path
from typing import Any

from src.config import Config
from src.constants import RAW_DATA_PATH
from src.riot_client import RiotClient
from src.utils import ensure_directory, save_json


class Extractor:
    """
    Extrai e salva partidas de jogadores configurados ou pesquisados.
    """

    def __init__(self, request_delay: float = 1.25) -> None:
        self.client = RiotClient()
        self.request_delay = max(request_delay, 0)

    def run(self) -> None:
        """Executa a extração dos jogadores configurados no .env."""

        for player in Config.PLAYERS:
            game_name = player.get("game_name")
            tag_line = player.get("tag_line")

            if not game_name or not tag_line:
                continue

            self.extract_player(
                game_name=game_name,
                tag_line=tag_line,
                match_count=Config.MATCH_COUNT
            )

    def extract_player(
        self,
        game_name: str,
        tag_line: str,
        match_count: int | None = None
    ) -> dict[str, Any]:
        """Extrai partidas de qualquer Riot ID e retorna um resumo."""

        game_name = game_name.strip()
        tag_line = tag_line.strip().removeprefix("#")

        if not game_name or not tag_line:
            raise ValueError(
                "O nome do jogador e a tag devem ser informados."
            )

        matches_to_fetch = (
            match_count
            if match_count is not None
            else Config.MATCH_COUNT
        )

        if matches_to_fetch < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )

        print()
        print("=" * 60)
        print(f"Extraindo partidas de {game_name}#{tag_line}")
        print("=" * 60)

        puuid = self.client.get_puuid(
            game_name=game_name,
            tag_line=tag_line
        )

        match_ids = self.client.get_match_ids(
            puuid,
            matches_to_fetch
        )

        player_folder = (
            Path(RAW_DATA_PATH)
            / self._build_player_slug(game_name, tag_line)
        )

        ensure_directory(str(player_folder))

        saved_count = 0
        existing_count = 0
        failed_matches: list[str] = []

        for match_id in match_ids:
            filepath = player_folder / f"{match_id}.json"

            if filepath.exists():
                existing_count += 1
                print(f"{match_id} já existe.")
                continue

            try:
                match = self.client.get_match_details(match_id)
                save_json(match, str(filepath))
                saved_count += 1
                print(f"{match_id} salvo.")

                if self.request_delay > 0:
                    time.sleep(self.request_delay)

            except RuntimeError as error:
                failed_matches.append(match_id)
                print(f"{match_id} não foi salvo: {error}")

                if "Limite de requisições" in str(error):
                    break

        print("-" * 60)
        print(f"Novas partidas salvas: {saved_count}")
        print(f"Partidas já existentes: {existing_count}")

        return {
            "game_name": game_name,
            "tag_line": tag_line,
            "puuid": puuid,
            "requested_count": matches_to_fetch,
            "match_ids_found": len(match_ids),
            "saved_count": saved_count,
            "existing_count": existing_count,
            "failed_matches": failed_matches,
            "player_folder": str(player_folder),
        }

    @staticmethod
    def _build_player_slug(game_name: str, tag_line: str) -> str:
        """Cria um nome de pasta seguro e único para o Riot ID."""

        raw_value = f"{game_name}_{tag_line}"
        normalized = unicodedata.normalize(
            "NFKD",
            raw_value
        ).encode(
            "ascii",
            "ignore"
        ).decode("ascii")

        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", normalized)
        return slug.strip("_").lower()
