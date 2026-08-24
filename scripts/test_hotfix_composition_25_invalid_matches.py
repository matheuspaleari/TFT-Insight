from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "scripts/diagnose_composition_intelligence_25_real.py"
text = FILE.read_text(encoding="utf-8")

checks = [
    ("Sintaxe válida", ast.parse(text) is not None),
    ("Busca candidatos extras", "requested * 2" in text),
    ("Ignora partida inválida", "[SKIP]" in text),
    ("Reconhece PUUID duplicado", "PUUIDs duplicados" in text),
    ("Não altera MatchTransformer", "class MatchTransformer" not in text),
    ("Exige mínimo analítico", "len(matches) < 3" in text),
    ("Mostra ignoradas no resumo", "Partidas ignoradas" in text),
    (
        "Continua usando CompositionHistoryAnalyzer",
        "CompositionHistoryAnalyzer.analyze" in text,
    ),
    (
        "Continua usando V2",
        "CompositionIntelligenceV2.build" in text,
    ),
]

print("=" * 96)
print("TFT INSIGHT - #25 HOTFIX INVALID MATCHES")
print("=" * 96)

passed = 0

for index, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{index}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 96)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#25 HOTFIX INVALID MATCHES: VALIDADO")
else:
    raise SystemExit(1)
