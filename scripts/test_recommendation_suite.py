from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.decision_engine import (
    CompositionHistoryAnalyzer,
    ContestHistoryAnalyzer,
    FlexHistoryAnalyzer,
)
from src.decision_engine.analyzers.strategic_decision_engine import (
    StrategicDecisionEngine,
)
from src.recommendation_engine import RecommendationEngine
from src.role_inference import (
    CommunityDragonItemParser,
    ItemCatalogClassifier,
    ItemObservationRepository,
    RichItemRepository,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


MATCH_COUNT = 20

OBSERVATIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "challenger"
    / "item_observations.json"
)


def main() -> None:
    game_name = input("Nome do jogador: ").strip()
    tag_line = input("Tag: ").strip()

    rich_repository = RichItemRepository()
    rich_items = CommunityDragonItemParser.parse(
        rich_repository.load()
    )

    observations = ItemObservationRepository(
        path=OBSERVATIONS_PATH
    ).load_all()

    classifications = ItemCatalogClassifier.classify_all(
        items=rich_items,
        observations=observations,
    )

    client = RiotClient()
    account = client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )
    puuid = account["puuid"]

    match_ids = client.get_match_ids(
        puuid=puuid,
        count=MATCH_COUNT,
    )

    matches = []

    for index, match_id in enumerate(match_ids, start=1):
        print(
            f"Processando partida {index}/{len(match_ids)}..."
        )

        try:
            matches.append(
                MatchTransformer.transform(
                    match_data=client.get_match_details(
                        match_id=match_id
                    ),
                    puuid=puuid,
                )
            )
        except (RuntimeError, ValueError, KeyError) as error:
            print(f"Partida ignorada: {error}")

    if not matches:
        raise RuntimeError(
            "Nenhuma partida válida foi processada."
        )

    strategic = StrategicDecisionEngine.analyze(
        matches,
        item_classifications=classifications,
    )

    contest = ContestHistoryAnalyzer.analyze(matches)

    flex = FlexHistoryAnalyzer.analyze(
        matches,
        item_classifications=classifications,
    )

    composition = CompositionHistoryAnalyzer.analyze(
        matches,
        contest_history=contest,
        item_classifications=classifications,
    )

    report = RecommendationEngine.analyze(
        strategic_report=strategic,
        contest_history=contest,
        flex_report=flex,
        composition_history=composition,
    )

    print()
    print("=" * 100)
    print("TFT INSIGHT - RECOMMENDATION SUITE")
    print("=" * 100)
    print(report.summary)

    print()
    print("ESTILO DE JOGO")
    print("-" * 100)
    print(
        f"Estilo principal : {report.playstyle.primary_style}"
    )
    print(
        f"Confiança        : {report.playstyle.confidence:.1f}%"
    )
    print(report.playstyle.explanation)

    print()
    print("PRIORIDADES")
    print("-" * 100)

    if report.priorities.recommendations:
        for index, item in enumerate(
            report.priorities.recommendations,
            start=1,
        ):
            print(
                f"{index}. [{item.priority.value}] "
                f"{item.category.value} — {item.title}"
            )
            print(f"   Ação: {item.action}")
            print(
                f"   Score atual: {item.current_score:.1f} | "
                f"Impacto: {item.impact_score:.1f} | "
                f"Confiança: {item.confidence:.1f}%"
            )
            print(
                f"   Ganho esperado: "
                f"{item.expected_placement_gain:.2f} colocação"
            )
    else:
        print("Nenhuma prioridade relevante.")

    print()
    print("RECOMENDAÇÃO DE CONTESTAÇÃO")
    print("-" * 100)
    print(f"Ação: {report.contest.action}")
    print(report.contest.explanation)

    print()
    print("RECOMENDAÇÃO DE ECONOMIA")
    print("-" * 100)
    print(f"Ação: {report.economy.action}")
    print(report.economy.explanation)

    print()
    print("COMPOSIÇÕES RECOMENDADAS")
    print("-" * 100)

    for item in report.compositions:
        print(
            f"{item.label:<16} "
            f"score={item.recommendation_score:>5.1f} "
            f"carry={item.carry_character_id:<24} "
            f"jogos={item.matches_played:<3} "
            f"top4={item.top4_rate:>5.1f}% "
            f"média={item.average_placement:.2f}"
        )

    print()
    print("✓ Recommendation Suite validada.")


if __name__ == "__main__":
    main()
