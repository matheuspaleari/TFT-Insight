from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.performance_engine.models import UnitSnapshot
from src.role_inference.models import UnitRoleSeed
from src.role_inference.repositories.unit_catalog_repository import (
    UnitCatalogRepository,
)
from src.role_inference.services.unit_role_seed_inference import (
    UnitRoleSeedInference,
)


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ERRO"
    print(f"{status:<5} {label}")
    if not condition:
        raise AssertionError(label)


def unit(character_id: str) -> UnitSnapshot:
    return UnitSnapshot(
        character_id=character_id,
        name="",
        rarity=0,
        tier=2,
        items=(),
    )


def main() -> None:
    print("=" * 100)
    print("TFT INSIGHT — UNIT CATALOG V2 — VALIDAÇÃO DE INTEGRAÇÃO")
    print("=" * 100)

    catalog = UnitCatalogRepository.load_all(
        force_reload=True
    )

    check(
        "catálogo possui 66 unidades",
        len(catalog) == 66,
    )

    check(
        "IDs únicos",
        len(catalog)
        == len(set(catalog)),
    )

    check(
        "todos possuem display_name",
        all(
            entry.display_name.strip()
            for entry in catalog.values()
        ),
    )

    check(
        "display_name não é o character_id",
        all(
            entry.display_name
            != entry.character_id
            for entry in catalog.values()
        ),
    )

    amumu = UnitRoleSeedInference.infer(
        unit=unit("DA_Amumu18"),
        classifications={},
    )

    check(
        "Amumu vem do catálogo como TANK mesmo sem itens",
        amumu.role == UnitRoleSeed.TANK,
    )

    master_yi = UnitRoleSeedInference.infer(
        unit=unit("DA_18_MasterYi_AD"),
        classifications={},
    )

    check(
        "Master Yi vem do catálogo como DAMAGE_CARRY mesmo sem itens",
        master_yi.role
        == UnitRoleSeed.DAMAGE_CARRY,
    )

    ivern = UnitRoleSeedInference.infer(
        unit=unit("DA_18_Ivern"),
        classifications={},
    )

    check(
        "Ivern vem do catálogo como SUPPORT",
        ivern.role == UnitRoleSeed.SUPPORT,
    )

    cinderling = UnitRoleSeedInference.infer(
        unit=unit("DA_Cinderling18"),
        classifications={},
    )

    check(
        "Cinderling permanece UNKNOWN",
        cinderling.role
        == UnitRoleSeed.UNKNOWN,
    )

    check(
        "nome de UI do Master Yi é limpo",
        UnitCatalogRepository.display_name(
            "DA_18_MasterYi_AD"
        )
        == "Master Yi",
    )

    check(
        "nome de UI do Amumu é limpo",
        UnitCatalogRepository.display_name(
            "DA_Amumu18"
        )
        == "Amumu",
    )

    check(
        "ID desconhecido nunca vaza automaticamente para UI",
        UnitCatalogRepository.display_name(
            "DA_QUALQUER_ID_INTERNO",
            fallback="",
        )
        == "Unidade",
    )

    print()
    print("RESULTADO: 9/9 OK")
    print(
        "Unit Catalog V2 carregado e priorizado "
        "no UnitRoleSeedInference."
    )


if __name__ == "__main__":
    main()
