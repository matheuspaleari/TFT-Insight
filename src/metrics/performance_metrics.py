"""
Métricas do TFT Insight Performance Score.
"""

from typing import Any


class PerformanceMetrics:
    """
    Calcula o TFT Insight Performance Score do jogador.
    """

    BASE_SCORE = 70.0

    REFERENCE_PLACEMENT = 4.5
    REFERENCE_TOP4_RATE = 50.0
    REFERENCE_LEVEL = 8.0
    REFERENCE_DAMAGE = 80.0

    def calculate(
        self,
        player_summary: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calcula o score geral e sua classificação.
        """

        self._validate_summary(player_summary)

        score_breakdown = {
            "base_score": self.BASE_SCORE,

            "placement_adjustment": (
                self._calculate_placement_adjustment(
                    player_summary["average_placement"]
                )
            ),

            "top4_adjustment": (
                self._calculate_top4_adjustment(
                    player_summary["top4_rate"]
                )
            ),

            "win_adjustment": (
                self._calculate_win_adjustment(
                    player_summary["win_rate"]
                )
            ),

            "level_adjustment": (
                self._calculate_level_adjustment(
                    player_summary["average_level"]
                )
            ),

            "damage_adjustment": (
                self._calculate_damage_adjustment(
                    player_summary["average_damage"]
                )
            ),
        }

        raw_score = sum(score_breakdown.values())

        performance_score = round(
            max(0, min(raw_score, 100))
        )

        status = self._get_status(
            performance_score
        )

        return {
            "performance_score": performance_score,
            "status": status,
            "score_breakdown": score_breakdown,
        }

    @staticmethod
    def _validate_summary(
        player_summary: dict[str, Any]
    ) -> None:
        """
        Verifica se todas as métricas necessárias estão presentes.
        """

        required_fields = {
            "average_placement",
            "top4_rate",
            "win_rate",
            "average_level",
            "average_damage",
        }

        missing_fields = required_fields.difference(
            player_summary.keys()
        )

        if missing_fields:
            fields = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Campos obrigatórios ausentes no resumo: "
                f"{fields}."
            )

    @classmethod
    def _calculate_placement_adjustment(
        cls,
        average_placement: float
    ) -> float:
        """
        Ajusta o score pela colocação média.

        Uma colocação menor é melhor.
        Cada posição de diferença vale quatro pontos.
        """

        adjustment = (
            cls.REFERENCE_PLACEMENT
            - average_placement
        ) * 4

        return round(
            max(-20, min(adjustment, 20)),
            2
        )

    @classmethod
    def _calculate_top4_adjustment(
        cls,
        top4_rate: float
    ) -> float:
        """
        Ajusta o score pela taxa de Top 4.
        """

        adjustment = (
            top4_rate
            - cls.REFERENCE_TOP4_RATE
        ) * 0.25

        return round(
            max(-12.5, min(adjustment, 12.5)),
            2
        )

    @staticmethod
    def _calculate_win_adjustment(
        win_rate: float
    ) -> float:
        """
        Adiciona bônus pela taxa de vitórias.

        Como vitórias são menos frequentes no TFT,
        uma taxa de 20% adiciona quatro pontos.
        """

        adjustment = win_rate * 0.2

        return round(
            max(0, min(adjustment, 8)),
            2
        )

    @classmethod
    def _calculate_level_adjustment(
        cls,
        average_level: float
    ) -> float:
        """
        Ajusta o score pelo nível médio.
        """

        adjustment = (
            average_level
            - cls.REFERENCE_LEVEL
        ) * 3

        return round(
            max(-6, min(adjustment, 6)),
            2
        )

    @classmethod
    def _calculate_damage_adjustment(
        cls,
        average_damage: float
    ) -> float:
        """
        Ajusta o score pelo dano médio aos adversários.
        """

        adjustment = (
            average_damage
            - cls.REFERENCE_DAMAGE
        ) * 0.05

        return round(
            max(-5, min(adjustment, 5)),
            2
        )

    @staticmethod
    def _get_status(
        performance_score: int
    ) -> dict[str, str]:
        """
        Retorna a classificação do score.
        """

        if performance_score >= 90:
            return {
                "label": "Excelente",
                "icon": "🟢",
                "description": (
                    "Desempenho muito acima da referência."
                ),
            }

        if performance_score >= 80:
            return {
                "label": "Muito Bom",
                "icon": "🟢",
                "description": (
                    "Desempenho forte e acima da média."
                ),
            }

        if performance_score >= 70:
            return {
                "label": "Bom",
                "icon": "🟡",
                "description": (
                    "Desempenho equilibrado, com espaço para evolução."
                ),
            }

        if performance_score >= 60:
            return {
                "label": "Regular",
                "icon": "🟠",
                "description": (
                    "Desempenho oscilante e com pontos importantes "
                    "para melhorar."
                ),
            }

        return {
            "label": "Precisa melhorar",
            "icon": "🔴",
            "description": (
                "Os resultados atuais indicam oportunidades "
                "significativas de evolução."
            ),
        }