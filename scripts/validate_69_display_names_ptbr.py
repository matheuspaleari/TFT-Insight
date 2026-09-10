from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_platform.utils.display_names import (
    friendly_game_name,
    friendly_item_name,
    friendly_public_text,
)


def check(label: str, condition: bool) -> bool:
    status = "OK" if condition else "FALHOU"
    print(f"[{status}] {label}")
    return bool(condition)


def main() -> int:
    print("=" * 92)
    print("VALIDACAO 69 - ROADMAP 25.1B: LOCALIZACAO PT-BR CENTRAL")
    print("=" * 92)

    checks = [
        check(
            "Sentry usa nome publico PT-BR Cascalho",
            friendly_game_name("DA_18_Sentry") == "Cascalho",
        ),
        check(
            "campeao comum continua amigavel",
            friendly_game_name("DA_18_Ahri") == "Ahri",
        ),
        check(
            "variante manual usa display_name do catalogo",
            friendly_game_name("DA_18_MasterYi_AD") == "Master Yi",
        ),
        check(
            "Adaptive Helm usa PT-BR do catalogo",
            friendly_item_name("DA_AdaptiveHelm") == "Elmo Adaptativo",
        ),
        check(
            "Archangels Staff usa PT-BR do catalogo",
            friendly_item_name("DA_ArchangelsStaff") == "Cajado do Arcanjo",
        ),
        check(
            "Jeweled Gauntlet usa PT-BR do catalogo",
            friendly_item_name("DA_JeweledGauntlet") == "Manopla Adornada",
        ),
        check(
            "item carry comum usa PT-BR",
            friendly_item_name("DA_SpearOfShojin") == "Lança de Shojin",
        ),
        check(
            "fallback de unidade desconhecida continua seguro",
            friendly_game_name("TFT18_ExemploTeste") == "Exemplo Teste",
        ),
        check(
            "fallback de item desconhecido continua seguro",
            friendly_item_name("DA_Item_ExampleThing") == "Example Thing",
        ),
        check(
            "texto publico converte Sentry para Cascalho",
            friendly_public_text(
                "Na partida, o carry foi DA_18_Sentry."
            )
            == "Na partida, o carry foi Cascalho.",
        ),
        check(
            "texto publico nao expoe ID tecnico",
            "DA_18_" not in friendly_public_text(
                "Linha centrada em DA_18_Ahri."
            ),
        ),
    ]

    print("-" * 92)
    passed = sum(checks)
    total = len(checks)
    print(f"Checks aprovados: {passed}/{total}")

    if passed == total:
        print("RESULTADO: LOCALIZACAO PT-BR CENTRAL VALIDADA")
        return 0

    print("RESULTADO: VALIDACAO 69 COM PENDENCIAS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
