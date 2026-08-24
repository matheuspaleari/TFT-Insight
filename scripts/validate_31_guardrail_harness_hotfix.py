from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/audit_31_general_guardrails.py"
text = path.read_text(encoding="utf-8")
ast.parse(text)

checks = [
    ("G01 presente", "G01_SYNTAX" in text),
    ("G02 presente", "G02_FORBIDDEN_CLAIM" in text),
    ("G02 reconhece negação", "_line_is_guardrail" in text),
    ("G02 ignora scripts/testes", "ignore_tokens" in text),
    ("G03 presente", "G03_REQUIRED_CONCEPT" in text),
    ("G04 presente", "G04_CRITICAL_FILE" in text),
    ("G05 presente", "G05_PROTECTED_FLAG" in text),
    ("G06 presente", "G06_SAMPLE_LANGUAGE" in text),
    ("G06 agora é por módulo", "SAMPLE_MODULES" in text),
    ("G06 aceita eligible_for_comparison", "eligible_for_comparison" in text),
    ("G07 presente", "G07_RANK_PREDICTION" in text),
    ("G08 presente", "G08_INTERNAL_LABEL" in text),
    ("Protege missão", "changes_mission" in text),
    ("Protege prioridade", "changes_learning_priority" in text),
    ("Protege evidence class", "changes_evidence_class" in text),
    ("Protege mission evidence", "counts_as_mission_evidence" in text),
    ("Protege rank up", "predicts_rank_up" in text),
    ("Audita scout", "scout_unknown" in text),
    ("Audita timing", "timing_unknown" in text),
    ("Modo strict", "--strict" in text),
    ("Gera JSON", "guardrail_audit_" in text),
    ("Não altera produto", "write_text" in text and "report_path" in text),
]

print("=" * 100)
print("#31 HOTFIX - VALIDAÇÃO DO HARNESS DE GUARDRAILS")
print("=" * 100)

passed = 0

for index, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{index}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#31 HOTFIX HARNESS: VALIDADO")
else:
    raise SystemExit(1)
