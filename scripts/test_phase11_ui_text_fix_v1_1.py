from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

page = (
    PROJECT_ROOT
    / "partner_platform/pages/benchmark_page.py"
)

engine = (
    PROJECT_ROOT
    / "src/coach_intelligence/services/coach_explanation_engine.py"
)

page_text = page.read_text(
    encoding="utf-8"
)
engine_text = engine.read_text(
    encoding="utf-8"
)

ast.parse(page_text)
ast.parse(engine_text)

checks = [
    (
        "UI traduz Tendência",
        "_LEARNING_TREND_LABELS.get" in page_text,
    ),
    (
        "BEGINNER possui label PT-BR",
        '"BEGINNER": "Iniciante"' in engine_text,
    ),
    (
        "INSUFFICIENT_HISTORY possui label PT-BR",
        '"INSUFFICIENT_HISTORY": "histórico insuficiente"' in engine_text,
    ),
    (
        "FOUNDATION possui label PT-BR",
        '"FOUNDATION": "Fundamentos"' in engine_text,
    ),
    (
        "Explicação continua determinística",
        "Produz explicação determinística" in engine_text,
    ),
]

print("=" * 82)
print("TFT INSIGHT - PHASE 11.7 UI TEXT FIX V1.1")
print("=" * 82)

passed = 0

for index, (name, ok) in enumerate(
    checks,
    start=1,
):
    passed += int(ok)
    print()
    print(f"[{index}] {name}")
    print(
        f"Status  : {'OK' if ok else 'ERRO'}"
    )

print()
print("=" * 82)
print(
    f"PASSARAM: {passed}/{len(checks)}"
)

if passed == len(checks):
    print(
        "PHASE 11.7 UI TEXT FIX V1.1: VALIDADO"
    )
    raise SystemExit(0)

raise SystemExit(1)
