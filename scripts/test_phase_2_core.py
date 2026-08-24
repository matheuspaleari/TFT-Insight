from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

load_dotenv(
    PROJECT_ROOT / ".env"
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
                    match_data=(
                        client.get_match_details(
                            match_id=match_id
                        )
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

    report = StrategicDecisionEngine.analyze(
        matches,
        item_classifications=classifications,
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT - FASE 2")
    print("=" * 80)
    print(
        f"Nota estratégica : "
        f"{report.overall_score:.2f}"
    )
    print(
        f"Classificação    : {report.label}"
    )

    print()
    print("ECONOMIA")
    print("-" * 80)
    print(
        f"Score            : "
        f"{report.economy.score:.2f}"
    )
    print(
        f"Nível médio      : "
        f"{report.economy.average_level:.2f}"
    )
    print(
        f"Taxa nível 8     : "
        f"{report.economy.level_8_rate:.2f}%"
    )
    print(
        report.economy.summary
    )

    print()
    print("ITEMIZAÇÃO")
    print("-" * 80)
    print(
        f"Score            : "
        f"{report.itemization.score:.2f}"
    )
    print(
        f"Carry 3 itens    : "
        f"{report.itemization.carry_full_item_rate:.2f}%"
    )
    print(
        f"Tank 3 itens     : "
        f"{report.itemization.tank_full_item_rate:.2f}%"
    )
    print(
        report.itemization.summary
    )

    print()
    print("TEMPO")
    print("-" * 80)
    print(
        f"Score            : "
        f"{report.tempo.score:.2f}"
    )
    print(
        f"Late game        : "
        f"{report.tempo.late_game_rate:.2f}%"
    )
    print(
        f"Saída precoce    : "
        f"{report.tempo.early_exit_rate:.2f}%"
    )
    print(
        report.tempo.summary
    )

    print()
    print("AUGMENTS")
    print("-" * 80)
    print(
        report.augment.summary
    )

    print()
    print("POSICIONAMENTO")
    print("-" * 80)
    print(
        report.positioning.summary
    )

    print()
    print("PRIORIDADES")
    print("-" * 80)

    if report.priorities:
        for priority in report.priorities:
            print(f"• {priority}")
    else:
        print("Nenhuma prioridade crítica.")

    print()
    print(
        "✓ Núcleo da Fase 2 validado."
    )


if __name__ == "__main__":
    main()
