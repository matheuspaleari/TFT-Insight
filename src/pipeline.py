"""
Pipeline principal do TFT Insight.
"""

from src.config import Config
from src.database import DatabaseManager
from src.extract import Extractor
from src.metrics.comparison_metrics import ComparisonMetrics
from src.metrics.player_metrics import PlayerMetrics
from src.metrics.trait_comparison import TraitComparison
from src.metrics.trait_metrics import TraitMetrics
from src.transform import Transformer
from src.views.terminal_view import TerminalView
from src.services.coach_service import CoachService
from src.metrics.performance_metrics import PerformanceMetrics
from src.metrics.trend_metrics import TrendMetrics


def run_pipeline() -> None:
    """
    Executa todas as etapas do pipeline.
    """

    extractor = Extractor()
    transformer = Transformer()
    database = DatabaseManager()

    extractor.run()
    transformer.run()
    database.run()

    player_metrics = PlayerMetrics()

    player_summary = player_metrics.get_summary(
        game_name=Config.PLAYER_GAME_NAME,
        tag_line=Config.PLAYER_TAG_LINE
    )

    performance_metrics = PerformanceMetrics()

    performance = performance_metrics.calculate(
        player_summary
    )

    trend_metrics = TrendMetrics()

    trend = trend_metrics.calculate(
        game_name=Config.PLAYER_GAME_NAME,
        tag_line=Config.PLAYER_TAG_LINE,
        match_count=Config.MATCH_COUNT
    )

    TerminalView.print_player_summary(
        summary=player_summary,
        performance=performance,
        trend=trend
    )

    comparison_metrics = ComparisonMetrics()

    comparison = comparison_metrics.compare(
        player_one=Config.PLAYERS[0],
        player_two=Config.PLAYERS[1]
    )

    TerminalView.print_comparison(
        comparison
    )

    trait_metrics = TraitMetrics()

    player_traits = trait_metrics.get_top_traits(
        game_name=Config.PLAYER_GAME_NAME,
        tag_line=Config.PLAYER_TAG_LINE,
        limit=10,
        active_only=False
    )

    master_traits = trait_metrics.get_top_traits(
        game_name=Config.MASTER_GAME_NAME,
        tag_line=Config.MASTER_TAG_LINE,
        limit=10,
        active_only=False
    )

    TerminalView.print_trait_summary(
        player_name=(
            f"{Config.PLAYER_GAME_NAME}"
            f"#{Config.PLAYER_TAG_LINE}"
        ),
        traits=player_traits
    )

    TerminalView.print_trait_summary(
        player_name=(
            f"{Config.MASTER_GAME_NAME}"
            f"#{Config.MASTER_TAG_LINE}"
        ),
        traits=master_traits
    )

    trait_comparison = TraitComparison()

    common_traits = trait_comparison.compare(
        player_one=Config.PLAYERS[0],
        player_two=Config.PLAYERS[1],
        limit=10
    )

    TerminalView.print_trait_comparison(
        player_one_name=(
            f"{Config.PLAYER_GAME_NAME}"
            f"#{Config.PLAYER_TAG_LINE}"
        ),
        player_two_name=(
            f"{Config.MASTER_GAME_NAME}"
            f"#{Config.MASTER_TAG_LINE}"
        ),
        comparisons=common_traits
    )

    coach_service = CoachService()

    player_insights = coach_service.generate_player_insights(
        comparison
    )

    trait_insights = coach_service.generate_trait_insights(
        comparisons=common_traits,
        minimum_uses=5,
        limit=5
    )

    TerminalView.print_player_insights(
        player_insights
    )

    TerminalView.print_coach_insights(
        trait_insights
    )