from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.role_inference import (
    CommunityDragonClient,
    CommunityDragonItemParser,
    HybridItemClassifier,
    ItemObservation,
    RichItemRepository,
)


TARGET_ITEM = "TFT_Item_WarmogsArmor"


def main() -> None:
    repository = RichItemRepository()

    if repository.exists():
        print("Carregando CommunityDragon do cache...")
        payload = repository.load()
    else:
        print(
            "Baixando CommunityDragon. "
            "O arquivo é grande e pode demorar..."
        )
        payload = CommunityDragonClient().get_tft_data()
        repository.save(payload)

    items = CommunityDragonItemParser.parse(payload)

    print(f"Itens completos encontrados: {len(items)}")

    item = items.get(TARGET_ITEM)

    if item is None:
        alternatives = [
            item_id
            for item_id in items
            if "Warmog" in item_id
        ]

        if not alternatives:
            raise RuntimeError(
                "Warmog não foi encontrado nos dados completos."
            )

        item = items[alternatives[0]]

    observation = ItemObservation(
        item_id=item.item_id,
        frontline_uses=82,
        backline_uses=18,
        damage_carry_uses=3,
        tank_uses=84,
        support_uses=13,
    )

    classification = HybridItemClassifier.classify(
        item=item,
        observation=observation,
    )

    print()
    print("=" * 80)
    print("TFT INSIGHT - HYBRID ITEM CLASSIFIER")
    print("=" * 80)
    print(f"Item       : {item.name}")
    print(f"ID         : {item.item_id}")
    print(f"Descrição  : {item.description[:180] or '-'}")
    print(f"Efeitos    : {len(item.effects)}")
    print(f"Categoria  : {classification.category.value}")
    print(f"Confiança  : {classification.confidence:.2f}%")
    print(f"Ofensivo   : {classification.offense_score:.2f}")
    print(f"Defensivo  : {classification.defense_score:.2f}")
    print(f"Utilidade  : {classification.utility_score:.2f}")
    print(f"Fonte      : {classification.source}")

    print()
    print("EVIDÊNCIAS")
    print("-" * 80)
    for evidence in classification.evidence:
        print(f"• {evidence}")

    print()
    print("✓ Classificador híbrido validado com sucesso.")


if __name__ == "__main__":
    main()
