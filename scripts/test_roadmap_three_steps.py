from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.decision_engine import (
    CompositionHistoryAnalyzer,
    FlexHistoryAnalyzer,
)
from src.role_inference import (
    CommunityDragonItemParser,
    ItemCatalogClassifier,
    ItemObservationRepository,
    RichItemRepository,
    RoleInferenceEngine,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


MATCH_COUNT = 10

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

    latest_player = matches[0].analyzed_participant

    if latest_player is None:
        raise RuntimeError(
            "Jogador da última partida não encontrado."
        )

    roles = RoleInferenceEngine.infer_participant(
        participant=latest_player,
        item_classifications=classifications,
    )

    composition = CompositionHistoryAnalyzer.analyze(
        matches,
        item_classifications=classifications,
    )

    flex = FlexHistoryAnalyzer.analyze(
        matches,
        item_classifications=classifications,
    )

    print()
    print("=" * 80)
    print("PASSO 1 — ROLE INFERENCE")
    print("=" * 80)
    print(
        "Carry: "
        f"{roles.damage_carry.character_id if roles.damage_carry else '-'}"
    )
    print(
        "Tank : "
        f"{roles.main_tank.character_id if roles.main_tank else '-'}"
    )
    print(
        "Sup. : "
        f"{roles.support.character_id if roles.support else '-'}"
    )

    latest = composition.latest_composition

    print()
    print("=" * 80)
    print("PASSO 2 — COMPOSITION IDENTITY V2")
    print("=" * 80)
    print(
        f"Traits : {', '.join(latest.trait_names) or '-'}"
    )
    print(
        f"Carry  : {latest.carry_character_id or '-'}"
    )
    print(
        f"Tank   : {latest.tank_character_id or '-'}"
    )
    print(
        f"Suporte: {latest.support_character_id or '-'}"
    )
    print(
        f"Core   : {', '.join(latest.unit_ids) or '-'}"
    )
    print(
        f"Composições únicas: "
        f"{composition.unique_compositions}"
    )

    print()
    print("=" * 80)
    print("PASSO 3 — FLEX ANALYZER")
    print("=" * 80)
    print(f"Score                  : {flex.score:.2f}")
    print(f"Classificação          : {flex.level.value}")
    print(
        f"Composições únicas     : "
        f"{flex.unique_compositions}"
    )
    print(
        f"Carries diferentes     : "
        f"{flex.unique_carries}"
    )
    print(
        f"Tanks diferentes       : "
        f"{flex.unique_tanks}"
    )
    print(
        f"Taxa de repetição      : "
        f"{flex.repetition_rate:.2f}%"
    )
    print(
        f"Força composição?      : "
        f"{'Possível padrão' if flex.likely_forces_composition else 'Não identificado'}"
    )

    print()
    print(
        "✓ Os três passos do roadmap foram validados."
    )


if __name__ == "__main__":
    main()
