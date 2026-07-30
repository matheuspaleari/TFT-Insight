"""
Apresentação dos resultados no terminal.
"""

from typing import Any
from src.ui.progress_bar import ProgressBar


class TerminalView:
    """
    Responsável por exibir relatórios no terminal.
    """

    @staticmethod
    def print_player_summary(
        summary: dict[str, Any],
        performance: dict[str, Any],
        trend: dict[str, Any]
    ) -> None:
        """
        Exibe o resumo individual e o Performance Score.
        """

        player_name = (
            f"{summary['game_name']}#{summary['tag_line']}"
        )

        status = performance["status"]

        print()
        print("=" * 80)
        print("TFT INSIGHT — RESUMO DO JOGADOR")
        print("=" * 80)

        print(f"Jogador: {player_name}")

        print()
        print("TFT Insight Performance Score")

        print(
            ProgressBar.render(
                value=performance["performance_score"],
                maximum=100,
                width=20
            )
        )

        print()

        print(
            f"Status:     "
            f"{status['icon']} {status['label']}"
        )

        print(
            f"Tendência:  "
            f"{trend['icon']} {trend['label']}"
        )

        print()
        print("-" * 80)

        print(f"Partidas analisadas: {summary['matches_played']}")
        print(f"Colocação média: {summary['average_placement']}")

        print(
            f"Top 4: {summary['top4_count']} "
            f"({summary['top4_rate']}%)"
        )

        print(
            f"Vitórias: {summary['wins']} "
            f"({summary['win_rate']}%)"
        )

        print(f"Nível médio: {summary['average_level']}")
        print(f"Dano médio: {summary['average_damage']}")

        print(
            "Ouro restante médio: "
            f"{summary['average_gold_left']}"
        )

    @staticmethod
    def print_comparison(
        comparison: dict[str, Any]
    ) -> None:
        """
        Exibe a comparação entre dois jogadores.
        """

        player_one = comparison["player_one"]
        player_two = comparison["player_two"]
        differences = comparison["differences"]

        player_one_name = (
            f"{player_one['game_name']}#{player_one['tag_line']}"
        )

        player_two_name = (
            f"{player_two['game_name']}#{player_two['tag_line']}"
        )

        print()
        print("=" * 80)
        print("TFT INSIGHT — COMPARAÇÃO ENTRE JOGADORES")
        print("=" * 80)

        print(
            f"{'Métrica':<28}"
            f"{player_one_name:>24}"
            f"{player_two_name:>24}"
        )

        print("-" * 80)

        TerminalView._print_row(
            "Partidas",
            player_one["matches_played"],
            player_two["matches_played"]
        )

        TerminalView._print_row(
            "Colocação média",
            player_one["average_placement"],
            player_two["average_placement"]
        )

        TerminalView._print_row(
            "Top 4",
            f"{player_one['top4_rate']}%",
            f"{player_two['top4_rate']}%"
        )

        TerminalView._print_row(
            "Vitórias",
            f"{player_one['win_rate']}%",
            f"{player_two['win_rate']}%"
        )

        TerminalView._print_row(
            "Nível médio",
            player_one["average_level"],
            player_two["average_level"]
        )

        TerminalView._print_row(
            "Dano médio",
            player_one["average_damage"],
            player_two["average_damage"]
        )

        TerminalView._print_row(
            "Ouro restante médio",
            player_one["average_gold_left"],
            player_two["average_gold_left"]
        )

        print()
        print("Principais diferenças")
        print("-" * 80)

        better_placement_player = differences[
            "better_placement_player"
        ]

        print(
            f"• {better_placement_player} possui colocação média "
            f"{differences['average_placement']:.2f} posição(ões) melhor."
        )

        print(
            "• Diferença de Top 4: "
            f"{differences['top4_rate']:.2f} pontos percentuais."
        )

        print(
            "• Diferença de vitórias: "
            f"{differences['win_rate']:.2f} pontos percentuais."
        )

        print(
            "• Diferença de nível médio: "
            f"{differences['average_level']:.2f}."
        )

        print(
            "• Diferença de dano médio: "
            f"{differences['average_damage']:.2f}."
        )

        print(
            f"• {differences['higher_gold_player']} termina com "
            f"{differences['average_gold_left']:.2f} de ouro a mais, "
            "em média."
        )

    @staticmethod
    def print_trait_summary(
        player_name: str,
        traits: list[dict[str, Any]]
    ) -> None:
        """
        Exibe as traits mais utilizadas por um jogador.
        """

        print()
        print("=" * 100)
        print(f"TFT INSIGHT — TRAITS MAIS UTILIZADAS — {player_name}")
        print("=" * 100)

        if not traits:
            print("Nenhuma trait encontrada.")
            return

        print(
            f"{'Trait':<26}"
            f"{'Usos':>8}"
            f"{'Média':>10}"
            f"{'Top 4':>12}"
            f"{'Vitórias':>12}"
            f"{'Unidades':>10}"
        )

        print("-" * 100)

        for trait in traits:
            trait_name = trait["trait_name"][:25]

            print(
                f"{trait_name:<26}"
                f"{trait['times_used']:>8}"
                f"{trait['average_placement']:>10}"
                f"{str(trait['top4_rate']) + '%':>12}"
                f"{str(trait['win_rate']) + '%':>12}"
                f"{trait['average_units']:>10}"
            )

    @staticmethod
    def print_trait_comparison(
        player_one_name: str,
        player_two_name: str,
        comparisons: list[dict[str, Any]]
    ) -> None:
        """
        Exibe a comparação das traits em comum.
        """

        print()
        print("=" * 110)
        print("TFT INSIGHT — COMPARAÇÃO DE TRAITS")
        print("=" * 110)

        if not comparisons:
            print("Nenhuma trait em comum foi encontrada.")
            return

        print(
            f"{'Trait':<22}"
            f"{player_one_name:>20}"
            f"{player_two_name:>20}"
            f"{'Top 4 Você':>14}"
            f"{'Top 4 Mestre':>16}"
        )

        print("-" * 110)

        for trait in comparisons:
            trait_name = trait["trait_name"][:21]

            print(
                f"{trait_name:<22}"
                f"{trait['player_one_average_placement']:>20}"
                f"{trait['player_two_average_placement']:>20}"
                f"{str(trait['player_one_top4_rate']) + '%':>14}"
                f"{str(trait['player_two_top4_rate']) + '%':>16}"
            )

    @staticmethod
    def print_player_insights(
        insights: list[str]
    ) -> None:
        """
        Exibe os insights gerais dos jogadores.
        """

        print()
        print("=" * 100)
        print("TFT INSIGHT — ANÁLISE GERAL")
        print("=" * 100)

        if not insights:
            print("Não foram encontradas diferenças relevantes.")
            return

        for insight in insights:
            print(f"• {insight}")

    @staticmethod
    def print_coach_insights(
        insights: list[dict[str, Any]]
    ) -> None:
        """
        Exibe os insights de traits gerados pelo Coach Service.
        """

        impact_icons = {
            "Muito Alto": "🔴",
            "Alto": "🟠",
            "Médio": "🟡",
            "Baixo": "🔵",
            "Muito Baixo": "🟢",
        }

        print()
        print("=" * 100)
        print("TFT INSIGHT — COACH DE TRAITS")
        print("=" * 100)

        if not insights:
            print(
                "Não foram encontradas diferenças relevantes "
                "com a amostra atual."
            )
            return

        for position, insight in enumerate(
            insights,
            start=1
        ):
            impact = insight["impact"]
            icon = impact_icons.get(impact, "⚪")

            print()
            print("-" * 100)
            print(f"{position}. {insight['trait_name']}")
            print(f"   Impacto: {icon} {impact}")

            print()
            print("   Você")
            print(
                f"   • Partidas: "
                f"{insight['player_one_uses']}"
            )
            print(
                f"   • Colocação média: "
                f"{insight['player_one_average_placement']}"
            )
            print(
                f"   • Top 4: "
                f"{insight['player_one_top4_rate']}%"
            )

            print()
            print("   Mestre")
            print(
                f"   • Partidas: "
                f"{insight['player_two_uses']}"
            )
            print(
                f"   • Colocação média: "
                f"{insight['player_two_average_placement']}"
            )
            print(
                f"   • Top 4: "
                f"{insight['player_two_top4_rate']}%"
            )

            print()
            print("   Análise")
            print(f"   • {insight['analysis']}")

            print()
            print("   Recomendação")
            print(f"   • {insight['recommendation']}")

        print()
        print("=" * 100)

    @staticmethod
    def _print_row(
        metric: str,
        player_one_value: Any,
        player_two_value: Any
    ) -> None:
        """
        Exibe uma linha da tabela comparativa.
        """

        print(
            f"{metric:<28}"
            f"{str(player_one_value):>24}"
            f"{str(player_two_value):>24}"
        )
