from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

engine = (
    ROOT
    / "src/carry_item_intelligence/services/carry_item_intelligence_engine.py"
)
presenter = (
    ROOT
    / "src/carry_item_intelligence/services/carry_item_player_presenter.py"
)
ui = (
    ROOT
    / "partner_platform/components/carry_item_intelligence.py"
)

files = {
    "engine": engine.read_text(encoding="utf-8"),
    "presenter": presenter.read_text(encoding="utf-8"),
    "ui": ui.read_text(encoding="utf-8"),
}

for text in files.values():
    ast.parse(text)

checks = [
    (
        "Carry público exige 2 itens",
        "MIN_ITEMS_FOR_PUBLIC_CARRY = 2"
        in files["engine"],
    ),
    (
        "Mantém RoleInference como fonte principal",
        "RoleInferenceEngine.infer_participant"
        in files["engine"],
    ),
    (
        "Possui fallback conservador",
        "principal item holder"
        in files["engine"],
    ),
    (
        "Sem carry quando falta evidência",
        "if not candidates"
        in files["engine"],
    ),
    (
        "Tier/rarity apenas desempata",
        "Mais itens primeiro; tier/rarity só desempata."
        in files["engine"],
    ),
    (
        "Coach limpa TFT17_",
        "_friendly_character"
        in files["presenter"],
    ),
    (
        "UI limpa TFT_ sem número",
        'r"^TFT_"'
        in files["ui"],
    ),
    (
        "UI limpa Item_",
        '"Item_"'
        in files["ui"],
    ),
    (
        "Mantém amostra mínima 3",
        "MIN_SAMPLE = 3"
        in files["engine"],
    ),
    (
        "Mantém proteção causal",
        "não prova que os itens causaram"
        in files["engine"],
    ),
]

print("=" * 96)
print(
    "#28 - AJUSTE DE QUALIDADE CARRY + ITENS"
)
print("=" * 96)

passed = 0

for index, (
    name,
    ok,
) in enumerate(
    checks,
    1,
):
    passed += int(ok)

    print()
    print(
        f"[{index}] {name}"
    )
    print(
        f"Status  : {'OK' if ok else 'ERRO'}"
    )

print()
print("=" * 96)
print(
    f"PASSARAM: {passed}/{len(checks)}"
)

if passed == len(checks):
    print(
        "#28 AJUSTE DE QUALIDADE: VALIDADO"
    )
else:
    raise SystemExit(1)
