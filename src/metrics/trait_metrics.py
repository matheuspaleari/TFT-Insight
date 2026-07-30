"""
Métricas relacionadas às traits dos jogadores.
"""

import sqlite3
from pathlib import Path
from typing import Any

from src.constants import DATABASE_PATH
from src.assets.trait_mapper import TraitMapper


class TraitMetrics:
    """
    Calcula métricas das traits utilizadas pelos jogadores.
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
        
        self.trait_mapper = TraitMapper()

    def get_top_traits(
        self,
        game_name: str,
        tag_line: str,
        limit: int = 10,
        active_only: bool = False
    ) -> list[dict[str, Any]]:
        """
        Retorna as traits mais utilizadas por um jogador.

        Args:
            game_name: Nome do jogador.
            tag_line: Tag do jogador.
            limit: Quantidade máxima de traits retornadas.
            active_only: Considera somente traits ativadas.
        """

        if not game_name or not tag_line:
            raise ValueError(
                "O nome do jogador e a tag devem ser informados."
            )

        if limit < 1:
            raise ValueError(
                "O limite deve ser maior que zero."
            )

        active_filter = (
            "AND t.style > 0"
            if active_only
            else ""
        )

        query = f"""
            SELECT
                t.trait_name,
                COUNT(*) AS times_used,
                ROUND(AVG(p.placement), 2) AS average_placement,
                SUM(
                    CASE
                        WHEN p.placement <= 4 THEN 1
                        ELSE 0
                    END
                ) AS top4_count,
                SUM(
                    CASE
                        WHEN p.placement = 1 THEN 1
                        ELSE 0
                    END
                ) AS wins,
                ROUND(AVG(t.num_units), 2) AS average_units,
                ROUND(AVG(t.tier_current), 2) AS average_tier
            FROM traits AS t
            INNER JOIN players AS p
                ON p.match_id = t.match_id
               AND p.puuid = t.puuid
            WHERE p.riot_id_game_name = ? COLLATE NOCASE
              AND p.riot_id_tagline = ? COLLATE NOCASE
              {active_filter}
            GROUP BY t.trait_name
            ORDER BY
                times_used DESC,
                average_placement ASC
            LIMIT ?
        """

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            results = connection.execute(
                query,
                (game_name, tag_line, limit)
            ).fetchall()

        traits: list[dict[str, Any]] = []

        for result in results:
            times_used = int(result["times_used"])
            top4_count = int(result["top4_count"] or 0)
            wins = int(result["wins"] or 0)

            traits.append(
                {
                    "trait_id": result["trait_name"],

                    "trait_name": self.trait_mapper.translate(
                        result["trait_name"]
                    ),

                    "times_used": times_used,

                    "average_placement": result[
                        "average_placement"
                    ],

                    "top4_count": top4_count,

                    "top4_rate": round(
                        (top4_count / times_used) * 100,
                        2
                    ),

                    "wins": wins,

                    "win_rate": round(
                        (wins / times_used) * 100,
                        2
                    ),

                    "average_units": result["average_units"],
                    "average_tier": result["average_tier"],
                }
            )

        return traits