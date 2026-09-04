from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts/analyze_tft_eog_schema.py"

text = ANALYZER.read_text(encoding="utf-8") if ANALYZER.exists() else ""

checks = [
    ("Analyzer presente", ANALYZER.exists()),
    ("Sintaxe valida", True),
    ("Nao usa requests", "requests" not in text),
    ("Nao usa rede", "http://" not in text and "https://" not in text),
    ("Le somente JSON local", "json.loads" in text),
    ("Procura tft_eog_stats", '"tft_eog_stats"' in text),
    ("Gera schema", "walk_schema" in text),
    ("Gera exemplos", "flatten_leaf_examples" in text),
    ("Mapeia jogadores", "player_summaries" in text),
    ("Mapeia board", "summarize_board" in text),
]

try:
    if ANALYZER.exists():
        ast.parse(text, filename=str(ANALYZER))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

print("=" * 108)
print("#63 / ROADMAP 25.0G - EOG SCHEMA ANALYZER GUARDRAILS")
print("=" * 108)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(
        f"[{i:02d}] "
        f"{label:<82} "
        f"{'OK' if ok else 'ERRO'}"
    )

print("-" * 108)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#63 ROADMAP 25.0G: EOG SCHEMA ANALYZER VALIDADO")
