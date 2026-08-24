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
from src.decision_engine.analyzers.decision_explanation_engine import (
    DecisionExplanationEngine,
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
    game_name = input(
        "Nome do jogador: "
    ).strip()
    tag_line = input(
        "Tag: "
    ).strip()

    rich_repository = RichItemRepository()

    if not rich_repository.exists():
        raise RuntimeError(
            "Cache do CommunityDragon não encontrado."
        )

    rich_items = CommunityDragonItemParser.parse(
        rich_repository.load()
    )

    observations = ItemObservationRepository(
        path=OBSERVATIONS_PATH
    ).load_all()

    if not observations:
        raise RuntimeError(
            "Observações Challenger não encontradas."
        )

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

    for index, match_id in enumerate(
        match_ids,
        start=1,
    ):
        print(
            f"Processando partida "
            f"{index}/{len(match_ids)}..."
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
        except (
            RuntimeError,
            ValueError,
            KeyError,
        ) as error:
            print(
                f"Partida ignorada: {error}"
            )

    if not matches:
        raise RuntimeError(
            "Nenhuma partida válida foi processada."
        )

    strategic = StrategicDecisionEngine.analyze(
        matches,
        item_classifications=classifications,
    )

    contest = ContestHistoryAnalyzer.analyze(
        matches
    )

    flex = FlexHistoryAnalyzer.analyze(
        matches,
        item_classifications=classifications,
    )

    composition = CompositionHistoryAnalyzer.analyze(
        matches,
        contest_history=contest,
        item_classifications=classifications,
    )

    explanation = DecisionExplanationEngine.explain(
        strategic_report=strategic,
        contest_history=contest,
        flex_report=flex,
        composition_history=composition,
    )

    print()
    print("=" * 90)
    print(
        "TFT INSIGHT - DECISION EXPLANATION ENGINE"
    )
    print("=" * 90)
    print(
        f"Nota        : {explanation.overall_score:.2f}"
    )
    print(
        f"Classificação: {explanation.label}"
    )
    print()
    print(explanation.headline)
    print()
    print(explanation.summary)

    print()
    print("PONTOS FORTES")
    print("-" * 90)

    if explanation.strengths:
        for strength in explanation.strengths:
            print(f"✓ {strength}")
    else:
        print("Nenhum ponto forte dominante.")

    print()
    print("PRIORIDADES")
    print("-" * 90)

    if explanation.priorities:
        for priority in explanation.priorities:
            print(f"• {priority}")
    else:
        print("Nenhuma prioridade crítica.")

    print()
    print("FATORES DETALHADOS")
    print("-" * 90)

    for factor in explanation.all_factors:
        score_text = (
            f"{factor.score:.2f}"
            if factor.score is not None
            else "-"
        )

        print(
            f"{factor.title:<18} "
            f"{factor.impact.value:<13} "
            f"score={score_text:<7} "
            f"peso={factor.weight:>6.1%} "
            f"contribuição={factor.contribution:>6.2f}"
        )

        print(
            f"  {factor.explanation}"
        )

        for evidence in factor.evidence:
            print(f"  - {evidence}")

    print()
    print("LIMITAÇÕES")
    print("-" * 90)

    for caveat in explanation.caveats:
        print(f"• {caveat}")

    print()
    print(
        "✓ DecisionExplanationEngine validado com sucesso."
    )


if __name__ == "__main__":
    main()
