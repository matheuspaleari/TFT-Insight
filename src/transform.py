"""
Camada responsável pela transformação dos dados brutos.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.constants import PROCESSED_DATA_PATH, RAW_DATA_PATH
from src.transformers.match_transformer import MatchTransformer
from src.transformers.player_transformer import PlayerTransformer
from src.transformers.trait_transformer import TraitTransformer
from src.transformers.unit_transformer import UnitTransformer
from src.utils import ensure_directory


class Transformer:
    """
    Orquestra a transformação dos arquivos JSON em CSV.
    """

    def run(self) -> None:
        """
        Executa a transformação dos dados.
        """

        matches_rows: list[dict[str, Any]] = []
        players_rows: list[dict[str, Any]] = []
        traits_rows: list[dict[str, Any]] = []
        units_rows: list[dict[str, Any]] = []

        raw_path = Path(RAW_DATA_PATH)
        processed_path = Path(PROCESSED_DATA_PATH)

        ensure_directory(processed_path)

        json_files = list(raw_path.rglob("*.json"))

        if not json_files:
            raise FileNotFoundError(
                "Nenhum arquivo JSON foi encontrado em data/raw."
            )

        for json_file in json_files:
            match_data = self._load_json(json_file)

            matches_rows.append(
                MatchTransformer.transform(match_data)
            )

            players_rows.extend(
                PlayerTransformer.transform(match_data)
            )

            traits_rows.extend(
                TraitTransformer.transform(match_data)
            )

            units_rows.extend(
                UnitTransformer.transform(match_data)
            )

        matches_df = pd.DataFrame(matches_rows)
        players_df = pd.DataFrame(players_rows)
        traits_df = pd.DataFrame(traits_rows)
        units_df = pd.DataFrame(units_rows)

        matches_df = matches_df.drop_duplicates(
            subset=["match_id"]
        )

        players_df = players_df.drop_duplicates(
            subset=["match_id", "puuid"]
        )

        traits_df = traits_df.drop_duplicates(
            subset=[
                "match_id",
                "puuid",
                "trait_name"
            ]
        )

        units_df = units_df.drop_duplicates(
            subset=[
                "match_id",
                "puuid",
                "unit_position"
            ]
        )

        self._save_csv(
            matches_df,
            processed_path / "matches.csv"
        )

        self._save_csv(
            players_df,
            processed_path / "players.csv"
        )

        self._save_csv(
            traits_df,
            processed_path / "traits.csv"
        )

        self._save_csv(
            units_df,
            processed_path / "units.csv"
        )

        print()
        print("=" * 60)
        print("Transformação concluída")
        print("=" * 60)
        print(f"Partidas processadas: {len(matches_df)}")
        print(f"Jogadores processados: {len(players_df)}")
        print(f"Traits processadas: {len(traits_df)}")
        print(f"Unidades processadas: {len(units_df)}")

    @staticmethod
    def _load_json(
        filepath: Path
    ) -> dict[str, Any]:
        """
        Lê um arquivo JSON.
        """

        with filepath.open(
            mode="r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    @staticmethod
    def _save_csv(
        dataframe: pd.DataFrame,
        filepath: Path
    ) -> None:
        """
        Salva um DataFrame em formato CSV.
        """

        dataframe.to_csv(
            filepath,
            index=False,
            encoding="utf-8-sig"
        )