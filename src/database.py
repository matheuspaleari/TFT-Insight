"""
Camada responsável pela persistência dos dados no SQLite.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from src.constants import PROCESSED_DATA_PATH


class DatabaseManager:
    """
    Gerencia a criação e a carga do banco SQLite.
    """

    def __init__(
        self,
        database_path: str = "database/tft_insight.db",
        schema_path: str = "database/schema.sql"
    ) -> None:
        self.database_path = Path(database_path)
        self.schema_path = Path(schema_path)

    def run(self) -> None:
        """
        Cria o banco e carrega os dados processados.
        """

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with sqlite3.connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON;")

            self._create_schema(connection)
            self._load_processed_data(connection)

        print()
        print("=" * 60)
        print("Carga no banco concluída")
        print("=" * 60)
        print(f"Banco criado em: {self.database_path}")

    def _create_schema(
        self,
        connection: sqlite3.Connection
    ) -> None:
        """
        Executa o arquivo schema.sql.
        """

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Arquivo de schema não encontrado: {self.schema_path}"
            )

        schema = self.schema_path.read_text(
            encoding="utf-8"
        )

        connection.executescript(schema)

    def _load_processed_data(
        self,
        connection: sqlite3.Connection
    ) -> None:
        """
        Carrega os CSVs processados no banco.
        """

        processed_path = Path(PROCESSED_DATA_PATH)

        tables = {
            "matches": processed_path / "matches.csv",
            "players": processed_path / "players.csv",
            "traits": processed_path / "traits.csv",
            "units": processed_path / "units.csv",
        }

        for table_name, csv_path in tables.items():
            if not csv_path.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {csv_path}"
                )

            dataframe = pd.read_csv(csv_path)

            dataframe.to_sql(
                name=table_name,
                con=connection,
                if_exists="append",
                index=False
            )

            print(
                f"Tabela {table_name}: "
                f"{len(dataframe)} registros carregados."
            )