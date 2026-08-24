from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

route_path = (
    ROOT
    / "src/integration_engine/api/routes/economy_intelligence.py"
)

text = route_path.read_text(
    encoding="utf-8"
)

checks = []

try:
    ast.parse(text)
    checks.append(
        (
            "Sintaxe da rota",
            True,
        )
    )
except SyntaxError:
    checks.append(
        (
            "Sintaxe da rota",
            False,
        )
    )

checks.extend(
    [
        (
            "Não importa EconomyHistoryAnalyzer do decision_engine raiz",
            "from src.decision_engine import EconomyHistoryAnalyzer"
            not in text,
        ),
        (
            "Importa analyzer do módulo exato",
            "from src.decision_engine.analyzers.economy_history_analyzer import"
            in text,
        ),
        (
            "Endpoint preservado",
            'prefix="/v1/economy-intelligence"'
            in text,
        ),
        (
            "Presenter preservado",
            "EconomyPlayerPresenter.build"
            in text,
        ),
    ]
)

try:
    module = importlib.import_module(
        "src.decision_engine.analyzers.economy_history_analyzer"
    )
    import_ok = hasattr(
        module,
        "EconomyHistoryAnalyzer",
    )
except Exception as error:
    print(
        "Erro ao importar analyzer:",
        error,
    )
    import_ok = False

checks.append(
    (
        "EconomyHistoryAnalyzer importável do módulo real",
        import_ok,
    )
)

print("=" * 96)
print(
    "TFT INSIGHT - #27 HOTFIX ECONOMY IMPORT"
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
print("=" * 96)
print(
    f"PASSARAM: "
    f"{passed}/{len(checks)}"
)

if passed == len(
    checks
):
    print(
        "#27 HOTFIX ECONOMY IMPORT: VALIDADO"
    )
else:
    raise SystemExit(1)
