from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

path = (
    ROOT
    / "scripts/audit_31_general_guardrails.py"
)

text = path.read_text(
    encoding="utf-8"
)

ast.parse(
    text
)

checks = [
    (
        "Audita sintaxe Python",
        "G01_SYNTAX"
        in text,
    ),
    (
        "Bloqueia causalidade inventada",
        "G02_FORBIDDEN_CLAIM"
        in text,
    ),
    (
        "Exige conceitos mínimos",
        "G03_REQUIRED_CONCEPT"
        in text,
    ),
    (
        "Valida arquivos críticos",
        "G04_CRITICAL_FILE"
        in text,
    ),
    (
        "Protege flags pedagógicas",
        "G05_PROTECTED_FLAG"
        in text,
    ),
    (
        "Audita linguagem de amostra",
        "G06_SAMPLE_LANGUAGE"
        in text,
    ),
    (
        "Bloqueia promessa de rank",
        "G07_RANK_PREDICTION"
        in text,
    ),
    (
        "Procura labels internas na UI",
        "G08_INTERNAL_LABEL"
        in text,
    ),
    (
        "Inclui missão protegida",
        "changes_mission"
        in text,
    ),
    (
        "Inclui prioridade protegida",
        "changes_learning_priority"
        in text,
    ),
    (
        "Inclui evidence class",
        "changes_evidence_class"
        in text,
    ),
    (
        "Inclui mission evidence",
        "counts_as_mission_evidence"
        in text,
    ),
    (
        "Inclui rank up",
        "predicts_rank_up"
        in text,
    ),
    (
        "Audita scout",
        "scout_unknown"
        in text,
    ),
    (
        "Audita timing",
        "timing_unknown"
        in text,
    ),
    (
        "Audita board final",
        "board_final"
        in text,
    ),
    (
        "Audita causalidade",
        "causality"
        in text,
    ),
    (
        "Audita tamanho de amostra",
        "sample_size"
        in text,
    ),
    (
        "Gera JSON",
        "guardrail_audit_"
        in text
        and ".json"
        in text,
    ),
    (
        "Possui modo strict",
        "--strict"
        in text,
    ),
]

print(
    "="
    * 100
)
print(
    "#31 / ROADMAP 20 - VALIDAÇÃO DO HARNESS DE GUARDRAILS"
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
        "#31 HARNESS DE GUARDRAILS: VALIDADO"
    )
else:
    raise SystemExit(
        1
    )
