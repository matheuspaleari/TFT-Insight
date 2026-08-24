from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

runner = (
    ROOT
    / "scripts/run_30_multi_player_validation.py"
)

text = runner.read_text(
    encoding="utf-8"
)

ast.parse(
    text
)

checks = [
    (
        "Usa quatro grupos competitivos",
        all(
            group
            in text
            for group in (
                "intermediate",
                "advanced",
                "expert",
                "elite",
            )
        ),
    ),
    (
        "Usa catálogos reais",
        "_player_catalog.json"
        in text,
    ),
    (
        "Testa Composições",
        "composition_intelligence"
        in text,
    ),
    (
        "Testa Contestação",
        "contest_intelligence"
        in text,
    ),
    (
        "Testa Economia",
        "economy_intelligence"
        in text,
    ),
    (
        "Testa Carries e Itens",
        "carry_item_intelligence"
        in text,
    ),
    (
        "Testa Coach consolidado",
        "build_pre_match_coach"
        in text,
    ),
    (
        "Protege foco",
        "Coach alterou o foco."
        in text,
    ),
    (
        "Protege missão",
        "Coach alterou a missão."
        in text,
    ),
    (
        "Valida identidade por jogador",
        "identity_matches"
        in text,
    ),
    (
        "Procura contaminação entre perfis",
        "fingerprints"
        in text,
    ),
    (
        "Valida ranges",
        "fora de 0..100"
        in text,
    ),
    (
        "Gera JSON",
        "multi_player_validation_"
        in text
        and ".json"
        in text,
    ),
    (
        "Gera CSV",
        ".csv"
        in text,
    ),
    (
        "Modo smoke usa 10 partidas",
        "default=10"
        in text,
    ),
    (
        "Possui pausa anti-rate-limit",
        "--sleep"
        in text,
    ),
    (
        "Não altera arquivos de produto",
        "write_text"
        in text
        and "data/diagnostics/multi_player_validation"
        in text,
    ),
]

print(
    "="
    * 100
)
print(
    "#30 / ROADMAP 19 - VALIDADOR DO HARNESS MULTI-JOGADOR"
)
print(
    "="
    * 100
)

passed = 0

for index, (
    name,
    ok,
) in enumerate(
    checks,
    1,
):
    passed += int(
        ok
    )

    print()
    print(
        f"[{index}] {name}"
    )
    print(
        f"Status  : "
        f"{'OK' if ok else 'ERRO'}"
    )

print()
print(
    "="
    * 100
)
print(
    f"PASSARAM: "
    f"{passed}/{len(checks)}"
)

if passed == len(
    checks
):
    print(
        "#30 HARNESS MULTI-JOGADOR: VALIDADO"
    )
else:
    raise SystemExit(
        1
    )
