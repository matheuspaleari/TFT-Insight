from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.performance_engine.models import ParticipantSnapshot, UnitSnapshot
from src.role_inference.models import UnitRole
from src.role_inference.services.role_inference_engine import RoleInferenceEngine


def check(label, condition):
    print(f"{'OK' if condition else 'ERRO':<5} {label}")
    if not condition:
        raise AssertionError(label)


def make_unit(character_id, tier=2, items=()):
    return UnitSnapshot(
        character_id=character_id,
        name="",
        rarity=0,
        tier=tier,
        items=tuple(items),
    )


def main():
    print("=" * 100)
    print("TFT INSIGHT — ROLE INFERENCE ENGINE V2")
    print("=" * 100)

    empty = {}

    amumu = RoleInferenceEngine.infer_unit(
        unit=make_unit("DA_Amumu18", tier=3),
        item_classifications=empty,
    )
    check("Amumu é TANK sem depender de itens", amumu.role == UnitRole.TANK)

    yi = RoleInferenceEngine.infer_unit(
        unit=make_unit("DA_18_MasterYi_AD", tier=2),
        item_classifications=empty,
    )
    check("Master Yi é DAMAGE_CARRY sem depender de itens", yi.role == UnitRole.DAMAGE_CARRY)

    ivern = RoleInferenceEngine.infer_unit(
        unit=make_unit("DA_18_Ivern", tier=2),
        item_classifications=empty,
    )
    check("Ivern é SUPPORT", ivern.role == UnitRole.SUPPORT)

    cinder = RoleInferenceEngine.infer_unit(
        unit=make_unit("DA_Cinderling18"),
        item_classifications=empty,
    )
    check("Cinderling continua UNKNOWN", cinder.role == UnitRole.UNKNOWN)

    # Mesmo com 3 IDs de itens sem classificação, Amumu não vira carry.
    amumu_items = RoleInferenceEngine.infer_unit(
        unit=make_unit(
            "DA_Amumu18",
            tier=3,
            items=("OFFENSE_A", "OFFENSE_B", "OFFENSE_C"),
        ),
        item_classifications=empty,
    )
    check("Amumu itemizado não vira carry", amumu_items.role != UnitRole.DAMAGE_CARRY)

    # Seleção entre dois carries válidos: estrelas podem desempatar/refinar.
    yi_2 = RoleInferenceEngine.infer_unit(
        unit=make_unit("DA_18_MasterYi_AD", tier=2),
        item_classifications=empty,
    )
    rengar_3 = RoleInferenceEngine.infer_unit(
        unit=make_unit("DA_18_Rengar", tier=3),
        item_classifications=empty,
    )
    selected = RoleInferenceEngine._select_main_role(
        assessments=(yi_2, rengar_3, amumu),
        role=UnitRole.DAMAGE_CARRY,
        score_name="offense_score",
    )
    check(
        "seleção principal só considera DAMAGE_CARRY",
        selected is not None and selected.character_id in {
            "DA_18_MasterYi_AD", "DA_18_Rengar"
        },
    )
    check(
        "Amumu nunca entra nos candidatos a carry",
        selected is None or selected.character_id != "DA_Amumu18",
    )

    no_carry = RoleInferenceEngine._select_main_role(
        assessments=(amumu, ivern),
        role=UnitRole.DAMAGE_CARRY,
        score_name="offense_score",
    )
    check("sem carry válido retorna None", no_carry is None)

    print()
    print("RESULTADO: 8/8 OK")


if __name__ == "__main__":
    main()
