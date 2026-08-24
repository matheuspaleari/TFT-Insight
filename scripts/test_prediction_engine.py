from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.decision_engine import (
    ContestHistoryAnalyzer,
    FlexHistoryAnalyzer,
)
from src.decision_engine.analyzers.prediction_engine import (
    PredictionEngine,
)
from src.decision_engine.analyzers.strategic_decision_engine import (
    StrategicDecisionEngine,
)
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

    prediction = PredictionEngine.predict(
        history_matches=matches,
        strategic_report=strategic,
        contest_history=contest,
        flex_report=flex,
    )

    print()
    print("=" * 90)
    print("TFT INSIGHT - PREDICTION ENGINE V1")
    print("=" * 90)
    print(
        f"Chance de Top 4       : "
        f"{prediction.top4_probability:.2f}%"
    )
    print(
        f"Chance de vitória     : "
        f"{prediction.win_probability:.2f}%"
    )
    print(
        f"Colocação esperada    : "
        f"{prediction.expected_placement:.2f}"
    )
    print(
        f"Risco                 : "
        f"{prediction.risk.value}"
    )
    print(
        f"Confiança da previsão : "
        f"{prediction.confidence:.2f}%"
    )

    print()
    print(prediction.summary)

    print()
    print("SINAIS POSITIVOS")
    print("-" * 90)

    for signal in prediction.positive_signals:
        print(f"✓ {signal}")

    print()
    print("SINAIS DE RISCO")
    print("-" * 90)

    if prediction.risk_signals:
        for signal in prediction.risk_signals:
            print(f"• {signal}")
    else:
        print("Nenhum risco histórico dominante.")

    print()
    print("LIMITAÇÕES")
    print("-" * 90)

    for caveat in prediction.caveats:
        print(f"• {caveat}")

    print()
    print("✓ PredictionEngine v1 validado.")


if __name__ == "__main__":
    main()
