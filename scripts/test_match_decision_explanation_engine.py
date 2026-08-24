from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.decision_engine import (
    ContestHistoryAnalyzer,
)
from src.decision_engine.analyzers.match_decision_explanation_engine import (
    MatchDecisionExplanationEngine,
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

    latest_match = matches[0]

    contest_history = ContestHistoryAnalyzer.analyze(
        matches
    )

    explanation = MatchDecisionExplanationEngine.explain(
        match=latest_match,
        history_matches=matches,
        item_classifications=classifications,
        contest_history=contest_history,
    )

    print()
    print("=" * 95)
    print(
        "TFT INSIGHT - MATCH DECISION EXPLANATION"
    )
    print("=" * 95)
    print(
        f"Partida       : {explanation.match_id}"
    )
    print(
        f"Colocação     : {explanation.placement}º"
    )
    print(
        f"Nota          : {explanation.overall_score:.2f}"
    )
    print(
        f"Classificação : {explanation.label}"
    )
    print()
    print(explanation.headline)
    print()
    print(explanation.summary)

    print()
    print("FATORES POSITIVOS")
    print("-" * 95)

    if explanation.positive_factors:
        for factor in explanation.positive_factors:
            print(
                f"✓ {factor.title}: "
                f"{factor.score:.1f}/100"
            )
            print(f"  {factor.explanation}")
    else:
        print("Nenhum fator positivo dominante.")

    print()
    print("PONTOS DE ATENÇÃO")
    print("-" * 95)

    combined_attention = (
        *explanation.critical_factors,
        *explanation.attention_factors,
    )

    if combined_attention:
        for factor in combined_attention:
            print(
                f"• {factor.title}: "
                f"{factor.score:.1f}/100"
            )
            print(f"  {factor.explanation}")
    else:
        print("Nenhum ponto crítico identificado.")

    print()
    print("FATORES DETALHADOS")
    print("-" * 95)

    for factor in explanation.all_factors:
        history_text = (
            f"{factor.historical_reference:.1f}"
            if factor.historical_reference is not None
            else "-"
        )

        difference_text = (
            f"{factor.difference_from_history:+.1f}"
            if factor.difference_from_history is not None
            else "-"
        )

        print(
            f"{factor.title:<28} "
            f"{factor.impact.value:<10} "
            f"score={factor.score:>5.1f} "
            f"hist={history_text:>5} "
            f"dif={difference_text:>6}"
        )

        for evidence in factor.evidence:
            print(f"  - {evidence}")

    print()
    print("RECOMENDAÇÕES")
    print("-" * 95)

    for recommendation in explanation.recommendations:
        print(f"• {recommendation}")

    print()
    print("LIMITAÇÕES")
    print("-" * 95)

    for caveat in explanation.caveats:
        print(f"• {caveat}")

    print()
    print(
        "✓ MatchDecisionExplanationEngine validado."
    )


if __name__ == "__main__":
    main()
