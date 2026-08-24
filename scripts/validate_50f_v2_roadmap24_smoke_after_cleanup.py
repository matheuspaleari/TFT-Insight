from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CRITICAL_FILES = (
    ROOT / "run_api.py",
    ROOT / "partner_platform/app.py",
    ROOT / "partner_platform/pages/home_page.py",
    ROOT / "partner_platform/pages/benchmark_page.py",
    ROOT / "partner_platform/platform_core/context.py",
    ROOT / "partner_platform/platform_core/router.py",
    ROOT / "partner_platform/navigation/catalog.py",
    ROOT / "src/integration_engine/api/app.py",
)

CRITICAL_IMPORTS = (
    "partner_platform.platform_core.context",
    "partner_platform.platform_core.router",
    "partner_platform.navigation.catalog",
    "partner_platform.pages.home_page",
    "partner_platform.pages.benchmark_page",
    "src.integration_engine.api.app",
)

OPTIONAL_TESTS = (
    "scripts/test_platform_imports.py",
    "scripts/test_platform_import_graph.py",
    "scripts/test_session_import_graph.py",
    "scripts/validate_48v2_roadmap23_final.py",
    "scripts/validate_49_roadmap24_public_contract.py",
)

checks: list[tuple[str, bool, str]] = []

for path in CRITICAL_FILES:
    checks.append((
        f"Arquivo crítico: {path.relative_to(ROOT)}",
        path.exists(),
        "",
    ))

syntax_errors = []
syntax_count = 0
for path in ROOT.rglob("*.py"):
    if "__pycache__" in path.parts:
        continue
    try:
        ast.parse(
            path.read_text(encoding="utf-8", errors="strict"),
            filename=str(path),
        )
        syntax_count += 1
    except Exception as error:
        syntax_errors.append(f"{path.relative_to(ROOT)}: {error}")

checks.append((
    f"Sintaxe Python ({syntax_count} arquivos)",
    not syntax_errors,
    "; ".join(syntax_errors[:5]),
))

sys.path.insert(0, str(ROOT))
for module_name in CRITICAL_IMPORTS:
    try:
        importlib.import_module(module_name)
        checks.append((f"Import: {module_name}", True, ""))
    except Exception as error:
        checks.append((f"Import: {module_name}", False, repr(error)))

for relative in OPTIONAL_TESTS:
    path = ROOT / relative
    if not path.exists():
        checks.append((f"Teste opcional ausente: {relative}", True, "ignorado"))
        continue

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    checks.append((
        f"Executa: {relative}",
        result.returncode == 0,
        result.stderr.strip() or result.stdout.strip()[-800:],
    ))

checks.extend((
    (
        "Auditoria final Roadmap 23 preservada",
        (ROOT / "scripts/validate_48v2_roadmap23_final.py").exists(),
        "",
    ),
    (
        "Auditoria pública Roadmap 24 preservada",
        (ROOT / "scripts/validate_49_roadmap24_public_contract.py").exists(),
        "",
    ),
    (
        "Último diagnóstico pós-partida v1_7 preservado",
        (ROOT / "scripts/diagnose_post_match_analysis_v1_7.py").exists(),
        "",
    ),
    (
        "Último teste pós-partida v1_7 preservado",
        (ROOT / "scripts/test_post_match_analysis_v1_7.py").exists(),
        "",
    ),
))

print("=" * 114)
print("#50F-V2 / ROADMAP 24.3B - SMOKE TEST PÓS-ARQUIVAMENTO")
print("=" * 114)

passed = 0
for index, (label, ok, detail) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{index:02d}] {label:<80} {'OK' if ok else 'ERRO'}")
    if not ok and detail:
        print(f"     {detail[:1000]}")

print("-" * 114)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    print("#50F-V2 ROADMAP 24.3B: REVISAR — MANTENHA O ARCHIVE")
    raise SystemExit(1)

print("#50F-V2 ROADMAP 24.3B: SMOKE TEST VALIDADO")
print("ARQUIVAMENTO NÃO QUEBROU A CAMADA PÚBLICA DO TFT INSIGHT")
