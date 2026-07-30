"""
Métricas de comparação entre jogadores.
"""

from typing import Any

from src.metrics.player_metrics import PlayerMetrics


class ComparisonMetrics:
    """
    Compara o desempenho de dois jogadores.
    """

    def __init__(self) -> None:
        self.player_metrics = PlayerMetrics()

    def compare(
        self,
        player_one: dict[str, str | None],
        player_two: dict[str, str | None]
    ) -> dict[str, Any]:
        """
        Compara dois jogadores com base nas métricas individuais.
        """

        self._validate_player(player_one)
        self._validate_player(player_two)

        summary_one = self.player_metrics.get_summary(
            game_name=str(player_one["game_name"]),
            tag_line=str(player_one["tag_line"])
        )

        summary_two = self.player_metrics.get_summary(
            game_name=str(player_two["game_name"]),
            tag_line=str(player_two["tag_line"])
        )

        return {
            "player_one": summary_one,
            "player_two": summary_two,
            "differences": self._calculate_differences(
                summary_one,
                summary_two
            ),
        }

    @staticmethod
    def _validate_player(
        player: dict[str, str | None]
    ) -> None:
        """
        Valida os dados necessários para consultar um jogador.
        """

        if not player.get("game_name") or not player.get("tag_line"):
            raise ValueError(
                "O nome e a tag dos dois jogadores devem ser informados."
            )

    @staticmethod
    def _calculate_differences(
        player_one: dict[str, Any],
        player_two: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calcula as diferenças entre os jogadores.
        """

        player_one_name = (
            f"{player_one['game_name']}#{player_one['tag_line']}"
        )

        player_two_name = (
            f"{player_two['game_name']}#{player_two['tag_line']}"
        )

        placement_difference = abs(
            player_one["average_placement"]
            - player_two["average_placement"]
        )

        top4_difference = abs(
            player_one["top4_rate"]
            - player_two["top4_rate"]
        )

        win_difference = abs(
            player_one["win_rate"]
            - player_two["win_rate"]
        )

        level_difference = abs(
            player_one["average_level"]
            - player_two["average_level"]
        )

        damage_difference = abs(
            player_one["average_damage"]
            - player_two["average_damage"]
        )

        gold_difference = abs(
            player_one["average_gold_left"]
            - player_two["average_gold_left"]
        )

        better_placement_player = (
            player_one_name
            if player_one["average_placement"]
            < player_two["average_placement"]
            else player_two_name
        )

        higher_gold_player = (
            player_one_name
            if player_one["average_gold_left"]
            > player_two["average_gold_left"]
            else player_two_name
        )

        return {
            "average_placement": round(
                placement_difference,
                2
            ),
            "top4_rate": round(top4_difference, 2),
            "win_rate": round(win_difference, 2),
            "average_level": round(level_difference, 2),
            "average_damage": round(damage_difference, 2),
            "average_gold_left": round(gold_difference, 2),
            "better_placement_player": better_placement_player,
            "higher_gold_player": higher_gold_player,
        }