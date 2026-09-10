from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.role_inference.models import UnitRole
from src.role_inference.services.item_catalog_classifier import (
    ItemCatalogClassifier,
)
from src.role_inference.services.role_inference_engine import (
    RoleInferenceEngine,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[OK] {label}")


def unit(
    character_id: str,
    *items: str,
    tier: int = 1,
    rarity: int = 1,
):
    return SimpleNamespace(
        character_id=character_id,
        items=tuple(items),
        tier=tier,
        rarity=rarity,
    )


def participant(puuid: str, *units):
    return SimpleNamespace(
        puuid=puuid,
        units=tuple(units),
    )


def main() -> None:
    print("=" * 88)
    print("VALIDAÇÃO 64 — ROLE INFERENCE V2 + AUTORIDADE ESTRUTURAL")
    print("=" * 88)

    classifications = ItemCatalogClassifier.classify_all(
        items={},
        observations={},
    )

    check(
        len(
            {
                item_id: value
                for item_id, value in classifications.items()
                if value.source == "manual_set18_catalog_v2"
            }
        )
        == 139,
        "139 itens manuais disponíveis para o RoleInference",
    )

    # 1) Tank nunca vira carry por itemização ofensiva.
    leona = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_Leona",
            "DA_InfinityEdge",
            "DA_Deathblade",
            "DA_LastWhisper",
            tier=3,
            rarity=5,
        ),
        item_classifications=classifications,
    )

    check(
        leona.role == UnitRole.TANK,
        "Leona permanece Tank mesmo com 3 itens ofensivos",
    )

    # 2) Support nunca vira carry por itemização ofensiva.
    ivern = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_Ivern",
            "DA_RabadonsDeathcap",
            "DA_JeweledGauntlet",
            "DA_SpearOfShojin",
            tier=3,
            rarity=5,
        ),
        item_classifications=classifications,
    )

    check(
        ivern.role == UnitRole.SUPPORT,
        "Ivern permanece Support mesmo com itens de carry",
    )

    # 3) Carry continua elegível sem item.
    teemo_no_items = RoleInferenceEngine.infer_unit(
        unit=unit("DA_18_Teemo"),
        item_classifications=classifications,
    )

    check(
        teemo_no_items.role == UnitRole.DAMAGE_CARRY,
        "Teemo continua Carry estrutural mesmo sem itens",
    )

    # 4) Itemização correta melhora ranking do carry.
    teemo_shojin = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_Teemo",
            "DA_SpearOfShojin",
            tier=2,
            rarity=2,
        ),
        item_classifications=classifications,
    )

    teemo_gargoyle = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_Teemo",
            "DA_GargoyleStoneplate",
            tier=2,
            rarity=2,
        ),
        item_classifications=classifications,
    )

    check(
        teemo_shojin.offense_score > teemo_gargoyle.offense_score,
        "item ofensivo favorece mais o carry que item de tank",
    )

    # 5) Dois carries: itemização deve ajudar a selecionar o correto.
    caitlyn_tank_item = unit(
        "DA_18_Caitlyn",
        "DA_GargoyleStoneplate",
        tier=2,
        rarity=2,
    )

    report = RoleInferenceEngine.infer_participant(
        participant=participant(
            "validation-64-player",
            caitlyn_tank_item,
            unit(
                "DA_18_Teemo",
                "DA_SpearOfShojin",
                tier=2,
                rarity=2,
            ),
        ),
        item_classifications=classifications,
    )

    check(
        report.damage_carry is not None,
        "participante com carries elegíveis possui carry principal",
    )

    check(
        report.damage_carry.character_id == "DA_18_Teemo",
        "entre dois carries válidos, itemização favorece Teemo",
    )

    # 6) Híbrido continua HYBRID, sem ser achatado para DAMAGE_CARRY.
    warwick = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_Warwick",
            "DA_Bloodthirster",
            tier=2,
            rarity=2,
        ),
        item_classifications=classifications,
    )

    check(
        warwick.role == UnitRole.HYBRID,
        "Warwick hybrid_ad_carry permanece HYBRID",
    )

    hybrid_report = RoleInferenceEngine.infer_participant(
        participant=participant(
            "validation-64-hybrid",
            unit(
                "DA_18_Warwick",
                "DA_Bloodthirster",
                tier=2,
                rarity=2,
            ),
            unit("DA_18_Leona"),
        ),
        item_classifications=classifications,
    )

    check(
        hybrid_report.damage_carry is not None
        and hybrid_report.damage_carry.character_id == "DA_18_Warwick",
        "híbrido carry_eligible pode disputar a rota de carry",
    )

    # 7) Híbrido tank pode disputar a rota de tank sem virar TANK puro.
    reksai = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_RekSai",
            "DA_GargoyleStoneplate",
            tier=2,
            rarity=1,
        ),
        item_classifications=classifications,
    )

    check(
        reksai.role == UnitRole.HYBRID,
        "Rek'Sai tank_hybrid permanece HYBRID",
    )

    tank_report = RoleInferenceEngine.infer_participant(
        participant=participant(
            "validation-64-tank-hybrid",
            unit(
                "DA_18_RekSai",
                "DA_GargoyleStoneplate",
                tier=2,
                rarity=1,
            ),
        ),
        item_classifications=classifications,
    )

    check(
        tank_report.main_tank is not None
        and tank_report.main_tank.character_id == "DA_18_RekSai",
        "híbrido tank pode disputar a rota de tank",
    )

    # 8) Unknown do catálogo permanece unknown mesmo com itens perfeitos.
    catalog_unknown = RoleInferenceEngine.infer_unit(
        unit=unit(
            "TFT18_Gromp",
            "DA_InfinityEdge",
            "DA_Deathblade",
            "DA_LastWhisper",
            tier=3,
            rarity=5,
        ),
        item_classifications=classifications,
    )

    check(
        catalog_unknown.role == UnitRole.UNKNOWN,
        "unidade manualmente UNKNOWN não vira carry por itens",
    )

    # 9) Unidade não catalogada também não pode virar carry.
    uncatalogued = RoleInferenceEngine.infer_unit(
        unit=unit(
            "DA_18_FutureUnit_NotCatalogued",
            "DA_InfinityEdge",
            "DA_Deathblade",
            "DA_LastWhisper",
            tier=3,
            rarity=5,
        ),
        item_classifications=classifications,
    )

    check(
        uncatalogued.role == UnitRole.UNKNOWN,
        "unidade fora do catálogo permanece UNKNOWN",
    )

    # 10) Nenhum fallback força carry quando só há tank/support/unknown.
    no_carry_report = RoleInferenceEngine.infer_participant(
        participant=participant(
            "validation-64-no-carry",
            unit("DA_18_Leona"),
            unit("DA_18_Ivern"),
            unit("TFT18_Gromp"),
        ),
        item_classifications=classifications,
    )

    check(
        no_carry_report.damage_carry is None,
        "nenhum fallback força carry quando não há candidato elegível",
    )

    # 11) Evidência do fluxo catalogado usa nome amigável.
    check(
        any("Teemo" in evidence for evidence in teemo_shojin.evidence),
        "evidência usa display_name amigável do campeão",
    )

    print()
    print(f"Teemo + Shojin    offense={teemo_shojin.offense_score:.2f}")
    print(f"Teemo + Gargoyle  offense={teemo_gargoyle.offense_score:.2f}")
    print(f"Warwick role       {warwick.role.value}")
    print(f"Rek'Sai role       {reksai.role.value}")
    print()
    print("=" * 88)
    print("RESULTADO: ROLE INFERENCE V2 ESTRUTURALMENTE CONSISTENTE")
    print("=" * 88)


if __name__ == "__main__":
    main()
