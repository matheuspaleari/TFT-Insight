"""
Comparação de traits entre dois jogadores.
"""

from typing import Any

from src.metrics.trait_metrics import TraitMetrics


class TraitComparison:
    """
    Compara o desempenho dos jogadores em traits em comum.
    """

    def __init__(self) -> None:
        self.trait_metrics = TraitMetrics()

    def compare(
        self,
        player_one: dict[str, str | None],
        player_two: dict[str, str | None],
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Compara as traits utilizadas pelos dois jogadores.
        """

        self._validate_player(player_one)
        self._validate_player(player_two)

        player_one_traits = self.trait_metrics.get_top_traits(
            game_name=str(player_one["game_name"]),
            tag_line=str(player_one["tag_line"]),
            limit=50,
            active_only=False
        )

        player_two_traits = self.trait_metrics.get_top_traits(
            game_name=str(player_two["game_name"]),
            tag_line=str(player_two["tag_line"]),
            limit=50,
            active_only=False
        )

        player_one_by_id = {
            trait["trait_id"]: trait
            for trait in player_one_traits
        }

        player_two_by_id = {
            trait["trait_id"]: trait
            for trait in player_two_traits
        }

        common_trait_ids = (
            player_one_by_id.keys()
            & player_two_by_id.keys()
        )

        comparison_rows: list[dict[str, Any]] = []

        for trait_id in common_trait_ids:
            trait_one = player_one_by_id[trait_id]
            trait_two = player_two_by_id[trait_id]

            comparison_rows.append(
                {
                    "trait_id": trait_id,
                    "trait_name": trait_one["trait_name"],

                    "player_one_times_used": trait_one[
                        "times_used"
                    ],
                    "player_two_times_used": trait_two[
                        "times_used"
                    ],

                    "player_one_average_placement": trait_one[
                        "average_placement"
                    ],
                    "player_two_average_placement": trait_two[
                        "average_placement"
                    ],

                    "player_one_top4_rate": trait_one[
                        "top4_rate"
                    ],
                    "player_two_top4_rate": trait_two[
                        "top4_rate"
                    ],

                    "average_placement_difference": round(
                        trait_one["average_placement"]
                        - trait_two["average_placement"],
                        2
                    ),

                    "top4_rate_difference": round(
                        trait_two["top4_rate"]
                        - trait_one["top4_rate"],
                        2
                    ),
                }
            )

        comparison_rows.sort(
            key=lambda row: (
                -(
                    row["player_one_times_used"]
                    + row["player_two_times_used"]
                ),
                row["player_two_average_placement"]
            )
        )

        return comparison_rows[:limit]

    @staticmethod
    def _validate_player(
        player: dict[str, str | None]
    ) -> None:
        """
        Valida os dados de um jogador.
        """

        if not player.get("game_name") or not player.get("tag_line"):
            raise ValueError(
                "O nome e a tag dos dois jogadores devem ser informados."
            )