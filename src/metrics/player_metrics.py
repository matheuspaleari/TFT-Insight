"""
Métricas relacionadas ao desempenho dos jogadores.
"""

import sqlite3
from pathlib import Path
from typing import Any

from src.constants import DATABASE_PATH


class PlayerMetrics:
    """
    Calcula métricas de desempenho a partir do banco SQLite.
    """

    def __init__(
        self,
        database_path: str = DATABASE_PATH
    ) -> None:
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Banco de dados não encontrado: {self.database_path}"
            )

    def get_summary(
        self,
        game_name: str,
        tag_line: str
    ) -> dict[str, Any]:
        """
        Retorna um resumo estatístico do jogador.
        """

        if not game_name or not tag_line:
            raise ValueError(
                "O nome do jogador e a tag devem ser informados."
            )

        query = """
            SELECT
                COUNT(*) AS matches_played,
                ROUND(AVG(placement), 2) AS average_placement,
                SUM(
                    CASE
                        WHEN placement <= 4 THEN 1
                        ELSE 0
                    END
                ) AS top4_count,
                SUM(
                    CASE
                        WHEN placement = 1 THEN 1
                        ELSE 0
                    END
                ) AS wins,
                ROUND(AVG(level), 2) AS average_level,
                ROUND(
                    AVG(total_damage_to_players),
                    2
                ) AS average_damage,
                ROUND(AVG(gold_left), 2) AS average_gold_left
            FROM players
            WHERE riot_id_game_name = ? COLLATE NOCASE
              AND riot_id_tagline = ? COLLATE NOCASE
        """

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            result = connection.execute(
                query,
                (game_name, tag_line)
            ).fetchone()

        if result is None or result["matches_played"] == 0:
            raise ValueError(
                f"Nenhuma partida encontrada para "
                f"{game_name}#{tag_line}."
            )

        matches_played = int(result["matches_played"])
        top4_count = int(result["top4_count"] or 0)
        wins = int(result["wins"] or 0)

        top4_rate = round(
            (top4_count / matches_played) * 100,
            2
        )

        win_rate = round(
            (wins / matches_played) * 100,
            2
        )

        return {
            "game_name": game_name,
            "tag_line": tag_line,
            "matches_played": matches_played,
            "average_placement": result["average_placement"],
            "top4_count": top4_count,
            "top4_rate": top4_rate,
            "wins": wins,
            "win_rate": win_rate,
            "average_level": result["average_level"],
            "average_damage": result["average_damage"],
            "average_gold_left": result["average_gold_left"],
        }

   