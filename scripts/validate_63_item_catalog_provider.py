from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.integration_engine.services.item_classification_provider import (
    ItemClassificationProvider,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[OK] {label}")


def main() -> None:
    print("=" * 88)
    print("VALIDAÇÃO 63 — PROVIDER REAL + ITEM CATALOG V2")
    print("=" * 88)

    # Garante que não estamos reutilizando estado de outro teste/processo.
    ItemClassificationProvider._classifications = None

    provider = ItemClassificationProvider(
        project_root=PROJECT_ROOT,
    )

    classifications = provider.get()

    check(
        isinstance(classifications, dict),
        "provider retornou um dicionário de classificações",
    )

    check(
        len(classifications) >= 139,
        "provider retornou pelo menos os 139 itens manuais",
    )

    manual = {
        item_id: classification
        for item_id, classification in classifications.items()
        if classification.source == "manual_set18_catalog_v2"
    }

    check(
        len(manual) == 139,
        "139 itens vieram do catálogo manual Set 18",
    )

    check(
        "DA_SpearOfShojin" in manual,
        "Lança de Shojin presente no provider real",
    )

    shojin = manual["DA_SpearOfShojin"]

    check(
        (
            shojin.offense_score,
            shojin.defense_score,
            shojin.utility_score,
        )
        == (100.0, 0.0, 15.0),
        "Lança de Shojin preserva 100/0/15 no provider",
    )

    gargoyle = manual["DA_GargoyleStoneplate"]

    check(
        (
            gargoyle.offense_score,
            gargoyle.defense_score,
            gargoyle.utility_score,
        )
        == (0.0, 100.0, 10.0),
        "Placa Gargolítica preserva 0/100/10 no provider",
    )

    shield = manual["DA_TacticiansShield"]

    check(
        (
            shield.offense_score,
            shield.defense_score,
            shield.utility_score,
        )
        == (50.0, 50.0, 50.0),
        "Escudo de Estrategista permanece neutro 50/50/50",
    )

    non_manual = {
        item_id: classification
        for item_id, classification in classifications.items()
        if classification.source != "manual_set18_catalog_v2"
    }

    print()
    print(f"Classificações totais : {len(classifications)}")
    print(f"Catálogo manual V2   : {len(manual)}")
    print(f"Fallback/legado      : {len(non_manual)}")

    if non_manual:
        print()
        print("Itens fora do catálogo manual:")
        for item_id, classification in sorted(non_manual.items()):
            print(
                f"  - {item_id} | "
                f"{classification.source} | "
                f"{classification.category.value}"
            )

    print()
    print("=" * 88)
    print("RESULTADO: PROVIDER REAL ESTÁ CONSUMINDO O ITEM CATALOG V2")
    print("=" * 88)


if __name__ == "__main__":
    main()
