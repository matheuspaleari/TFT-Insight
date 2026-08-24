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


from src.role_inference import (
    CommunityDragonClient,
    CommunityDragonItemParser,
    RichItemRepository,
)
from src.role_inference.repositories import (
    ItemObservationRepository,
)
from src.role_inference.services.item_learning_cycle import (
    ItemLearningCycle,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


MATCH_COUNT = 10


def main() -> None:
    game_name = input(
        "Nome do jogador: "
    ).strip()
    tag_line = input(
        "Tag: "
    ).strip()

    rich_repository = RichItemRepository()

    if rich_repository.exists():
        payload = rich_repository.load()
    else:
        print(
            "Baixando CommunityDragon..."
        )
        payload = (
            CommunityDragonClient()
            .get_tft_data()
        )
        rich_repository.save(payload)

    rich_items = (
        CommunityDragonItemParser.parse(
            payload
        )
    )

    riot_client = RiotClient()

    account = riot_client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    puuid = account["puuid"]

    match_ids = riot_client.get_match_ids(
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
            match_data = (
                riot_client.get_match_details(
                    match_id=match_id,
                )
            )

            matches.append(
                MatchTransformer.transform(
                    match_data=match_data,
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

    classifications, observations = (
        ItemLearningCycle(
            observation_repository=(
                ItemObservationRepository()
            )
        ).run(
            matches=matches,
            items=rich_items,
        )
    )

    observed = [
        observation
        for observation in observations.values()
        if (
            observation.damage_carry_uses
            or observation.tank_uses
            or observation.support_uses
        )
    ]

    observed.sort(
        key=lambda observation: (
            observation.damage_carry_uses
            + observation.tank_uses
            + observation.support_uses
        ),
        reverse=True,
    )

    print()
    print("=" * 80)
    print(
        "TFT INSIGHT - ITEM OBSERVATION COLLECTOR"
    )
    print("=" * 80)
    print(
        f"Partidas analisadas   : "
        f"{len(matches)}"
    )
    print(
        f"Itens classificados   : "
        f"{len(classifications)}"
    )
    print(
        f"Itens com observações : "
        f"{len(observed)}"
    )

    print()
    print("PRINCIPAIS OBSERVAÇÕES")
    print("-" * 80)

    for observation in observed[:15]:
        classification = (
            classifications.get(
                observation.item_id
            )
        )

        print(
            f"{observation.item_id:<42} "
            f"carry={observation.damage_carry_uses:<3} "
            f"tank={observation.tank_uses:<3} "
            f"support={observation.support_uses:<3} "
            f"→ "
            f"{classification.category.value if classification else '-'}"
        )

    print()
    print(
        "✓ ItemObservationCollector validado com sucesso."
    )


if __name__ == "__main__":
    main()
