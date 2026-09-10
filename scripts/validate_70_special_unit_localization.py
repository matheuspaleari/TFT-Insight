from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "role_inference" / "set18" / "unit_catalog_v2.json"

# Nomes que já têm evidência suficiente para tratamento público.
# "confirmed_ptbr" não altera o catálogo; esta auditoria é somente leitura.
KNOWN_PUBLIC_NAMES = {
    "DA_18_Sentry": ("Cascalho", "CONFIRMADO_PTBR"),
    "DA_18_ElderDragon": ("Dragão Ancião", "CONFIRMADO_PTBR"),
}

# Casos que sabemos que merecem revisão, mas não vamos traduzir no chute.
REVIEW_IDS = {
    "DA_Sentinel18",
    "DA_Krug18",
    "DA_Brambleback18",
    "DA_Cinderling18",
    "DA_CrimsonRaptor18",
    "DA_Scuttlecrab18",
    "DA_Murkwolf18",
    "DA_Gromp18_AP",
    "TFT18_Gromp",
}


def main() -> int:
    if not CATALOG.exists():
        print(f"[FALHOU] Catálogo não encontrado: {CATALOG}")
        return 1

    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    units = payload.get("units", [])

    specials = [
        unit
        for unit in units
        if str(unit.get("unit_type", "")).lower() in {"special", "special_variant"}
    ]

    print("=" * 118)
    print("AUDITORIA 70 - LOCALIZACAO DE UNIDADES ESPECIAIS DO SET 18")
    print("=" * 118)
    print(f"Catálogo: {CATALOG}")
    print(f"Unidades totais: {len(units)}")
    print(f"Especiais / variantes especiais: {len(specials)}")
    print("-" * 118)
    print(f"{'STATUS':<20} {'CHARACTER_ID':<30} {'ATUAL':<22} {'PUBLICO/ALVO'}")
    print("-" * 118)

    counts = {
        "CONFIRMADO_PTBR": 0,
        "REVISAR_PTBR": 0,
        "MANTER_POR_ENQUANTO": 0,
    }

    for unit in sorted(specials, key=lambda x: str(x.get("character_id", ""))):
        cid = str(unit.get("character_id", "")).strip()
        current = str(unit.get("display_name", "")).strip()

        if cid in KNOWN_PUBLIC_NAMES:
            target, status = KNOWN_PUBLIC_NAMES[cid]
        elif cid in REVIEW_IDS:
            target, status = "-", "REVISAR_PTBR"
        else:
            target, status = current or "-", "MANTER_POR_ENQUANTO"

        counts[status] += 1
        print(f"{status:<20} {cid:<30} {current:<22} {target}")

    print("-" * 118)
    print("RESUMO")
    print(f"  Confirmados PT-BR      : {counts['CONFIRMADO_PTBR']}")
    print(f"  Precisam revisão PT-BR : {counts['REVISAR_PTBR']}")
    print(f"  Manter por enquanto    : {counts['MANTER_POR_ENQUANTO']}")
    print()
    print("POLÍTICA")
    print("  - Esta auditoria NÃO altera unit_catalog_v2.json.")
    print("  - Nenhum nome em REVISAR_PTBR deve ser traduzido automaticamente.")
    print("  - Correções só entram após validação do nome público PT-BR.")
    print("  - character_id continua sendo identificador interno; nunca deve aparecer na UI.")
    print()
    print("RESULTADO: AUDITORIA DE UNIDADES ESPECIAIS GERADA SEM ALTERAR O CATÁLOGO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
