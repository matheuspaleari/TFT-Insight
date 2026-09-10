from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.role_inference.models import ItemCategory
from src.role_inference.repositories.item_manual_catalog_repository import (
    ItemManualCatalogRepository,
)
from src.role_inference.services.item_catalog_classifier import (
    ItemCatalogClassifier,
)


def check(
    condition: bool,
    label: str,
) -> None:
    if not condition:
        raise AssertionError(label)

    print(f"[OK] {label}")


def main() -> None:
    print("=" * 88)
    print("VALIDAÇÃO 62 — ITEM CATALOG V2 + AUTORIDADE MANUAL")
    print("=" * 88)

    repository = ItemManualCatalogRepository()

    check(
        repository.exists(),
        "item_catalog_v2.json encontrado",
    )

    payload = repository.load()
    catalog = repository.load_items()

    check(
        payload["schema_version"] == "2.0",
        "schema_version 2.0",
    )

    check(
        len(catalog) == 139,
        "139 riot_item_id únicos",
    )

    classifications = ItemCatalogClassifier.classify_all(
        items={},
        observations={},
    )

    check(
        len(classifications) == 139,
        "classificador expõe os 139 itens mesmo sem CommunityDragon",
    )

    gargoyle = classifications[
        "DA_GargoyleStoneplate"
    ]
    check(
        gargoyle.category == ItemCategory.DEFENSE
        and gargoyle.offense_score == 0
        and gargoyle.defense_score == 100
        and gargoyle.utility_score == 10,
        "Placa Gargolítica preserva 0/100/10",
    )

    shojin = classifications[
        "DA_SpearOfShojin"
    ]
    check(
        shojin.category == ItemCategory.OFFENSE
        and shojin.offense_score == 100
        and shojin.defense_score == 0
        and shojin.utility_score == 15,
        "Lança de Shojin preserva 100/0/15",
    )

    shield = classifications[
        "DA_TacticiansShield"
    ]
    check(
        shield.category == ItemCategory.HYBRID
        and shield.offense_score == 50
        and shield.defense_score == 50
        and shield.utility_score == 50,
        "Escudo de Estrategista é neutro 50/50/50",
    )

    for item_id in (
        "DA_TacticiansCape",
        "DA_TacticiansCrown",
        "DA_TacticiansShield",
    ):
        item = catalog[item_id]
        check(
            item["learning_enabled"] is False,
            f"{item['display_name']}: aprendizado desativado",
        )

    emblem_ids = [
        item_id
        for item_id, item in catalog.items()
        if item.get("manual_category") == "emblem"
    ]

    check(
        bool(emblem_ids),
        "emblemas detectados no catálogo",
    )

    check(
        all(
            catalog[item_id]["carry_weight"] == 50
            and catalog[item_id]["tank_weight"] == 50
            and catalog[item_id]["support_weight"] == 50
            and catalog[item_id]["learning_enabled"] is False
            for item_id in emblem_ids
        ),
        "todos os emblemas são 50/50/50 sem aprendizado",
    )

    radiant_items = [
        item
        for item in catalog.values()
        if item.get("classification_rule")
        == "radiant_inherits_verified_base"
    ]

    check(
        bool(radiant_items),
        "Radiantes com herança de item-base encontrados",
    )

    for radiant in radiant_items:
        base_id = radiant["inherits_from"]
        base = catalog[base_id]

        check(
            (
                radiant["carry_weight"],
                radiant["tank_weight"],
                radiant["support_weight"],
            )
            == (
                base["carry_weight"],
                base["tank_weight"],
                base["support_weight"],
            ),
            (
                f"{radiant['display_name']} herda "
                f"os pesos de {base['display_name']}"
            ),
        )

    forbidden = catalog[
        "DA_Artifact_ForbiddenIdol"
    ]

    check(
        (
            forbidden["carry_weight"],
            forbidden["tank_weight"],
            forbidden["support_weight"],
        )
        == (5, 5, 100),
        "Ídolo Proibido mantém decisão manual Support 5/5/100",
    )

    sources = {
        classification.source
        for classification in classifications.values()
    }

    check(
        sources == {"manual_set18_catalog_v2"},
        "catálogo manual é a fonte dos 139 itens revisados",
    )

    print()
    print("=" * 88)
    print("RESULTADO: ITEM CATALOG V2 INTEGRADO E CONSISTENTE")
    print("=" * 88)


if __name__ == "__main__":
    main()
