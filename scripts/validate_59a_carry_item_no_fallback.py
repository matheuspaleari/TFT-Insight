from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.carry_item_intelligence.services.carry_item_intelligence_engine import (
    CarryItemIntelligenceEngine,
)


def unit(character_id: str, items=(), tier: int = 1, rarity: int = 0):
    return SimpleNamespace(
        character_id=character_id,
        items=tuple(items),
        tier=tier,
        rarity=rarity,
    )


def participant(*units):
    return SimpleNamespace(units=tuple(units))


def assessment(character_id: str, items=()):
    return SimpleNamespace(
        character_id=character_id,
        item_ids=tuple(items),
    )


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "FALHOU"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    # 1) Sem carry inferido: um tank full item NÃO pode virar carry por fallback.
    board = participant(
        unit(
            "DA_Amumu18",
            ("ITEM_TANK_A", "ITEM_TANK_B", "ITEM_TANK_C"),
            tier=3,
            rarity=4,
        ),
        unit("DA_18_Ivern", ("ITEM_SUPPORT_A",)),
    )
    selected = CarryItemIntelligenceEngine._validated_carry(
        participant=board,
        assessment=None,
    )
    check("sem damage_carry retorna None", selected is None)

    # 2) Carry válido com 2+ itens é preservado.
    board = participant(
        unit("DA_18_MasterYi_AD", ("ITEM_AD_A", "ITEM_AD_B")),
        unit("DA_Amumu18", ("ITEM_TANK_A", "ITEM_TANK_B", "ITEM_TANK_C")),
    )
    selected = CarryItemIntelligenceEngine._validated_carry(
        participant=board,
        assessment=assessment(
            "DA_18_MasterYi_AD",
            ("ITEM_AD_A", "ITEM_AD_B"),
        ),
    )
    check(
        "carry inferido com 2 itens é preservado",
        selected == (
            "DA_18_MasterYi_AD",
            ("ITEM_AD_A", "ITEM_AD_B"),
        ),
    )

    # 3) Carry inferido com menos de 2 itens não é substituído por item holder.
    board = participant(
        unit("DA_18_MasterYi_AD", ("ITEM_AD_A",)),
        unit(
            "DA_Amumu18",
            ("ITEM_TANK_A", "ITEM_TANK_B", "ITEM_TANK_C"),
            tier=3,
            rarity=4,
        ),
    )
    selected = CarryItemIntelligenceEngine._validated_carry(
        participant=board,
        assessment=assessment(
            "DA_18_MasterYi_AD",
            ("ITEM_AD_A",),
        ),
    )
    check(
        "carry com 1 item retorna None sem escolher outro holder",
        selected is None,
    )

    # 4) O ID pode ser resolvido do assessment e os itens recuperados do board.
    board = participant(
        unit("DA_18_Rengar", ("ITEM_AD_A", "ITEM_AD_B", "ITEM_AD_C")),
    )
    selected = CarryItemIntelligenceEngine._validated_carry(
        participant=board,
        assessment=assessment("DA_18_Rengar"),
    )
    check(
        "itens podem ser recuperados do board para o carry inferido",
        selected == (
            "DA_18_Rengar",
            ("ITEM_AD_A", "ITEM_AD_B", "ITEM_AD_C"),
        ),
    )

    # 5) Assessment sem identidade não autoriza fallback pelo board.
    board = participant(
        unit("DA_18_Rammus", ("ITEM_TANK_A", "ITEM_TANK_B", "ITEM_TANK_C")),
    )
    selected = CarryItemIntelligenceEngine._validated_carry(
        participant=board,
        assessment=SimpleNamespace(item_ids=()),
    )
    check(
        "assessment sem identidade não autoriza fallback",
        selected is None,
    )

    print()
    print("RESULTADO: 5/5 OK")
    print("Carry Item Intelligence respeita o RoleInferenceEngine V2 como fonte única de carry.")


if __name__ == "__main__":
    main()
