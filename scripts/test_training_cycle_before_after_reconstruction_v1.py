from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

paths = [
    ROOT / "src/integration_engine/services/cached_match_service.py",
    ROOT / "src/training/services/training_cycle_window_service.py",
    ROOT / "scripts/diagnose_training_cycle_before_after_v1.py",
]

checks = []

for path in paths:
    source = path.read_text(encoding="utf-8")
    ast.parse(source)
    checks.append((f"{path.name}: sintaxe", True))

cached = paths[0].read_text(encoding="utf-8")
window = paths[1].read_text(encoding="utf-8")
diagnostic = paths[2].read_text(encoding="utf-8")

checks += [
    (
        "CachedMatchService possui load_matches_by_ids",
        "def load_matches_by_ids(" in cached,
    ),
    (
        "WindowService usa baseline_match_ids",
        '"baseline_match_ids"' in window,
    ),
    (
        "WindowService usa completed_match_ids",
        '"completed_match_ids"' in window,
    ),
    (
        "Diagnóstico calcula BEFORE/AFTER",
        "before_performance" in diagnostic
        and "after_performance" in diagnostic,
    ),
    (
        "Diagnóstico não decide resultado",
        "POSITIVE" not in diagnostic
        and "NEGATIVE" not in diagnostic
        and "INCONCLUSIVE" not in diagnostic,
    ),
]

print("=" * 82)
print("TFT INSIGHT - BEFORE/AFTER RECONSTRUCTION V1")
print("=" * 82)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{i}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 82)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("BEFORE/AFTER RECONSTRUCTION V1: VALIDADO")
    raise SystemExit(0)

print("BEFORE/AFTER RECONSTRUCTION V1: AJUSTE NECESSÁRIO")
raise SystemExit(1)
