from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.role_inference.models import ItemObservation
from src.role_inference.repositories.item_manual_catalog_repository import (
    ItemManualCatalogRepository,
)
from src.role_inference.services.item_catalog_classifier import (
    ItemCatalogClassifier,
)
from src.role_inference.services.item_observation_collector import (
    ItemObservationCollector,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[OK] {label}")


def unit(character_id: str, *items: str):
    return SimpleNamespace(
        character_id=character_id,
        items=tuple(items),
        tier=2,
        rarity=2,
    )


def match_with(*units):
    participant = SimpleNamespace(
        puuid="validation-65",
        units=tuple(units),
    )
    return SimpleNamespace(participants=(participant,))


def total(obs: ItemObservation | None) -> int:
    if obs is None:
        return 0
    return (
        obs.damage_carry_uses
        + obs.tank_uses
        + obs.support_uses
    )


def main() -> None:
    print("=" * 88)
    print("VALIDAÇÃO 65 — LEARNING_ENABLED + OBSERVATION COLLECTOR")
    print("=" * 88)

    catalog = ItemManualCatalogRepository().load_items()
    classifications = ItemCatalogClassifier.classify_all(
        items={},
        observations={},
    )

    check(len(catalog) == 139, "catálogo manual contém 139 itens")

    disabled = {
        item_id
        for item_id, entry in catalog.items()
        if entry["learning_enabled"] is False
    }
    enabled = set(catalog) - disabled

    check(bool(disabled), "existem itens com aprendizado desativado")
    check(bool(enabled), "existem itens com aprendizado habilitado")

    for item_id in (
        "DA_TacticiansCrown",
        "DA_TacticiansCape",
        "DA_TacticiansShield",
    ):
        check(
            item_id in disabled,
            f"{catalog[item_id]['display_name']}: aprendizado desativado",
        )

    emblems = {
        item_id
        for item_id, entry in catalog.items()
        if entry["item_type"] == "emblem_or_trait"
        and item_id != "DA_Component_Spatula"
    }
    check(bool(emblems), "emblemas encontrados")
    check(
        emblems <= disabled,
        "todos os emblemas estão fora do aprendizado",
    )

    check(
        catalog["DA_Component_Spatula"]["learning_enabled"] is False,
        "Espátula preserva regra manual sem aprendizado",
    )

    # Um item habilitado e um desabilitado na mesma unidade-carry.
    enabled_item = "DA_SpearOfShojin"
    disabled_item = "DA_TacticiansCrown"

    check(
        catalog[enabled_item]["learning_enabled"] is True,
        "Lança de Shojin está habilitada para observação secundária",
    )

    existing = {
        enabled_item: ItemObservation(
            item_id=enabled_item,
            damage_carry_uses=10,
        ),
        disabled_item: ItemObservation(
            item_id=disabled_item,
            damage_carry_uses=7,
        ),
    }

    result = ItemObservationCollector.collect(
        matches=[
            match_with(
                unit(
                    "DA_18_Teemo",
                    enabled_item,
                    disabled_item,
                )
            )
        ],
        item_classifications=classifications,
        existing=existing,
    )

    check(
        total(result[enabled_item]) == 11,
        "item learning_enabled=True recebe nova observação",
    )
    check(
        total(result[disabled_item]) == 7,
        "item learning_enabled=False não recebe nova observação",
    )

    # O collector não deve apagar histórico existente automaticamente.
    check(
        disabled_item in result,
        "histórico antigo de item desabilitado é preservado",
    )

    # Item fora do catálogo continua compatível com o comportamento legado.
    legacy_item = "VALIDATION_65_LEGACY_ITEM"
    legacy_classifications = dict(classifications)
    legacy_classifications[legacy_item] = classifications[enabled_item]

    legacy_result = ItemObservationCollector.collect(
        matches=[
            match_with(
                unit(
                    "DA_18_Teemo",
                    legacy_item,
                )
            )
        ],
        item_classifications=legacy_classifications,
        existing={},
    )

    check(
        total(legacy_result.get(legacy_item)) == 1,
        "item fora do catálogo mantém coleta legado/fallback",
    )

    print()
    print(f"Itens manuais             : {len(catalog)}")
    print(f"Learning habilitado       : {len(enabled)}")
    print(f"Learning desabilitado     : {len(disabled)}")
    print(f"Emblemas fora do learning : {len(emblems)}")
    print()
    print("=" * 88)
    print("RESULTADO: LEARNING_ENABLED RESPEITADO NA COLETA")
    print("=" * 88)


if __name__ == "__main__":
    main()
