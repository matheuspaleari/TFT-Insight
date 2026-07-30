"""
Métricas de tendência e evolução do jogador.
"""

import sqlite3
from pathlib import Path
from typing import Any

from src.constants import DATABASE_PATH


class TrendMetrics:
    """
    Compara partidas antigas e recentes para identificar a tendência.
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

    def calculate(
        self,
        game_name: str,
        tag_line: str,
        match_count: int = 20
    ) -> dict[str, Any]:
        """
        Calcula a tendência de desempenho do jogador.

        As partidas são divididas em dois grupos:

        - período recente;
        - período anterior.
        """

        if not game_name or not tag_line:
            raise ValueError(
                "O nome do jogador e a tag devem ser informados."
            )

        if match_count < 4:
            raise ValueError(
                "São necessárias pelo menos quatro partidas."
            )

        matches = self._get_matches(
            game_name=game_name,
            tag_line=tag_line,
            match_count=match_count
        )

        if len(matches) < 4:
            return self._insufficient_data_result(
                matches_found=len(matches)
            )

        window_size = len(matches) // 2

        recent_matches = matches[:window_size]
        previous_matches = matches[window_size:window_size * 2]

        recent_summary = self._calculate_period_summary(
            recent_matches
        )

        previous_summary = self._calculate_period_summary(
            previous_matches
        )

        differences = self._calculate_differences(
            previous=previous_summary,
            recent=recent_summary
        )

        trend_score = self._calculate_trend_score(
            differences
        )

        classification = self._classify_trend(
            trend_score
        )

        details = self._build_details(
            differences=differences
)

        return {
            "label": classification["label"],
            "icon": classification["icon"],
            "color": classification["color"],
            "description": classification["description"],
            "trend_score": trend_score,
            "matches_analyzed": len(matches),
            "matches_per_period": window_size,
            "previous": previous_summary,
            "recent": recent_summary,
            "differences": differences,
            "details": details,
            "has_enough_data": True,
        }

    def _get_matches(
        self,
        game_name: str,
        tag_line: str,
        match_count: int
    ) -> list[dict[str, Any]]:
        """
        Busca as partidas mais recentes do jogador.
        """

        query = """
            SELECT
                p.placement,
                p.level,
                p.total_damage_to_players,
                m.game_datetime,
                m.game_creation
            FROM players AS p
            INNER JOIN matches AS m
                ON m.match_id = p.match_id
            WHERE p.riot_id_game_name = ? COLLATE NOCASE
              AND p.riot_id_tagline = ? COLLATE NOCASE
            ORDER BY
                COALESCE(
                    m.game_datetime,
                    m.game_creation
                ) DESC
            LIMIT ?
        """

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            results = connection.execute(
                query,
                (game_name, tag_line, match_count)
            ).fetchall()

        return [
            {
                "placement": int(result["placement"]),
                "level": float(result["level"] or 0),
                "damage": float(
                    result["total_damage_to_players"] or 0
                ),
            }
            for result in results
        ]

    @staticmethod
    def _calculate_period_summary(
        matches: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calcula as métricas de um período.
        """

        total_matches = len(matches)

        placements = [
            match["placement"]
            for match in matches
        ]

        levels = [
            match["level"]
            for match in matches
        ]

        damages = [
            match["damage"]
            for match in matches
        ]

        top4_count = sum(
            1
            for placement in placements
            if placement <= 4
        )

        wins = sum(
            1
            for placement in placements
            if placement == 1
        )

        return {
            "matches": total_matches,
            "average_placement": round(
                sum(placements) / total_matches,
                2
            ),
            "top4_rate": round(
                (top4_count / total_matches) * 100,
                2
            ),
            "win_rate": round(
                (wins / total_matches) * 100,
                2
            ),
            "average_level": round(
                sum(levels) / total_matches,
                2
            ),
            "average_damage": round(
                sum(damages) / total_matches,
                2
            ),
        }

    @staticmethod
    def _calculate_differences(
        previous: dict[str, Any],
        recent: dict[str, Any]
    ) -> dict[str, float]:
        """
        Calcula a evolução do período recente.

        Na colocação, um valor positivo significa melhora,
        pois uma colocação menor é melhor.
        """

        return {
            "placement": round(
                previous["average_placement"]
                - recent["average_placement"],
                2
            ),
            "top4_rate": round(
                recent["top4_rate"]
                - previous["top4_rate"],
                2
            ),
            "win_rate": round(
                recent["win_rate"]
                - previous["win_rate"],
                2
            ),
            "average_level": round(
                recent["average_level"]
                - previous["average_level"],
                2
            ),
            "average_damage": round(
                recent["average_damage"]
                - previous["average_damage"],
                2
            ),
        }

    @staticmethod
    def _calculate_trend_score(
        differences: dict[str, float]
    ) -> float:
        """
        Calcula um indicador combinado de tendência.

        A colocação e o Top 4 possuem maior peso.
        """

        placement_component = (
            differences["placement"] * 2
        )

        top4_component = (
            differences["top4_rate"] / 20
        )

        level_component = (
            differences["average_level"] * 1.5
        )

        damage_component = (
            differences["average_damage"] / 25
        )

        trend_score = (
            placement_component
            + top4_component
            + level_component
            + damage_component
        )

        return round(trend_score, 2)

    @staticmethod
    def _build_details(
        differences: dict[str, float]
    ) -> list[str]:
        """
        Cria explicações sobre as mudanças entre os períodos.
        """

        details: list[str] = []

        placement_difference = differences["placement"]

        if placement_difference >= 0.2:
            details.append(
                "A colocação média melhorou "
                f"{placement_difference:.2f} posição(ões)."
            )

        elif placement_difference <= -0.2:
            details.append(
                "A colocação média piorou "
                f"{abs(placement_difference):.2f} posição(ões)."
            )

        top4_difference = differences["top4_rate"]

        if top4_difference >= 5:
            details.append(
                "A taxa de Top 4 aumentou "
                f"{top4_difference:.2f} pontos percentuais."
            )

        elif top4_difference <= -5:
            details.append(
                "A taxa de Top 4 caiu "
                f"{abs(top4_difference):.2f} pontos percentuais."
            )

        level_difference = differences["average_level"]

        if level_difference >= 0.2:
            details.append(
                "O nível médio aumentou "
                f"{level_difference:.2f}."
            )

        elif level_difference <= -0.2:
            details.append(
                "O nível médio caiu "
                f"{abs(level_difference):.2f}."
            )

        damage_difference = differences["average_damage"]

        if damage_difference >= 5:
            details.append(
                "O dano médio aumentou "
                f"{damage_difference:.2f}."
            )

        elif damage_difference <= -5:
            details.append(
                "O dano médio caiu "
                f"{abs(damage_difference):.2f}."
            )

        if not details:
            details.append(
                "As principais métricas permaneceram próximas "
                "entre os dois períodos."
            )

        return details

    @staticmethod
    def _classify_trend(
        trend_score: float
    ) -> dict[str, str]:
        """
        Converte o indicador numérico em uma classificação.
        """

        if trend_score >= 2:
            return {
                "label": "Evolução forte",
                "icon": "📈",
                "color": "green",
                "description": (
                    "As partidas recentes apresentam uma melhora "
                    "clara em relação ao período anterior."
                ),
            }

        if trend_score >= 0.5:
            return {
                "label": "Evoluindo",
                "icon": "📈",
                "color": "green",
                "description": (
                    "O desempenho recente indica uma evolução gradual."
                ),
            }

        if trend_score > -0.5:
            return {
                "label": "Estável",
                "icon": "➡️",
                 "color": "yellow",
                "description": (
                    "Não houve uma mudança relevante entre os períodos."
                ),
            }

        if trend_score > -2:
            return {
                "label": "Em queda",
                "icon": "📉",
                 "color": "orange",
                "description": (
                    "As partidas recentes apresentam uma redução "
                    "moderada de desempenho."
                ),
            }

        return {
            "label": "Queda acentuada",
            "icon": "📉",
            "color": "red",
            "description": (
                "As partidas recentes apresentam uma queda relevante "
                "em relação ao período anterior."
            ),
        }

    @staticmethod
    def _insufficient_data_result(
        matches_found: int
    ) -> dict[str, Any]:
        """
        Retorna uma resposta quando não há partidas suficientes.
        """

        return {
            "label": "Dados insuficientes",
            "icon": "⚪",
            "color": "gray",
            "description": (
                "São necessárias pelo menos quatro partidas "
                "para calcular a tendência."
            ),
            "trend_score": 0,
            "matches_analyzed": matches_found,
            "matches_per_period": 0,
            "previous": {},
            "recent": {},
            "differences": {},
            "details": [],
            "has_enough_data": False,
        }