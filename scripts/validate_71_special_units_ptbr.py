from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from partner_platform.utils.display_names import friendly_game_name

CATALOG = ROOT / "data" / "role_inference" / "set18" / "unit_catalog_v2.json"

EXPECTED = {
    "DA_18_Sentry": "Cascalho",
    "DA_18_ElderDragon": "Dragão Ancião",
    "DA_Brambleback18": "Rubrivira",
    "DA_Cinderling18": "Rubrivirim",
    "DA_CrimsonRaptor18": "Mamãe Bicuda",
    "DA_Gromp18_AP": "Grompe",
    "DA_Krug18": "Krugue",
    "DA_Murkwolf18": "Lobo Trevoguari",
    "DA_Scuttlecrab18": "Aronguejo",
    "DA_Sentinel18": "Azuporã",
    "TFT18_Gromp": "Grompe",
}

def check(label: str, ok: bool) -> bool:
    print(f"[{'OK' if ok else 'FALHOU'}] {label}")
    return ok

def main() -> int:
    print("=" * 100)
    print("VALIDACAO 71 - ROADMAP 25.1C: UNIDADES ESPECIAIS PT-BR")
    print("=" * 100)

    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    units = {
        str(u.get("character_id")): u
        for u in payload.get("units", [])
        if isinstance(u, dict)
    }

    checks = []

    for cid, expected in EXPECTED.items():
        unit = units.get(cid)
        checks.append(
            check(
                f"{cid} catalogo -> {expected}",
                unit is not None and unit.get("display_name") == expected,
            )
        )
        checks.append(
            check(
                f"{cid} UI -> {expected}",
                friendly_game_name(cid) == expected,
            )
        )

    technical_names = {
        "Sentry",
        "Elder Dragon",
        "Brambleback",
        "Cinderling",
        "Crimson Raptor",
        "Gromp",
        "Krug",
        "Murkwolf",
        "Scuttlecrab",
        "Sentinel",
    }

    special_public_names = {
        str(u.get("display_name", "")).strip()
        for u in units.values()
        if str(u.get("unit_type", "")).lower() in {"special", "special_variant"}
    }

    checks.append(
        check(
            "nenhuma unidade especial auditada mantém nome técnico/inglês antigo",
            not bool(technical_names & special_public_names),
        )
    )

    passed = sum(checks)
    total = len(checks)

    print("-" * 100)
    print(f"Checks aprovados: {passed}/{total}")

    if passed == total:
        print("RESULTADO: LOCALIZACAO DAS UNIDADES ESPECIAIS VALIDADA")
        return 0

    print("RESULTADO: VALIDACAO 71 COM PENDENCIAS")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
