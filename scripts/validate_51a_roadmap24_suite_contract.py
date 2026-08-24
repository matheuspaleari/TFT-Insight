from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
runner = ROOT / "scripts/validate_51_roadmap24_official_suite.py"
docs = ROOT / "docs/VALIDATION.md"


checks = (
    (
        "Runner oficial presente",
        runner.exists(),
    ),
    (
        "Documentação de validação presente",
        docs.exists(),
    ),
)


runner_text = (
    runner.read_text(
        encoding="utf-8"
    )
    if runner.exists()
    else ""
)


docs_text = (
    docs.read_text(
        encoding="utf-8"
    )
    if docs.exists()
    else ""
)


if runner_text:
    ast.parse(
        runner_text,
        filename=str(runner),
    )


extended = (
    *checks,
    (
        "Perfil quick definido",
        '"quick"' in runner_text,
    ),
    (
        "Perfil full definido",
        '"full"' in runner_text,
    ),
    (
        "Sintaxe global incluída",
        "def _check_syntax()" in runner_text,
    ),
    (
        "Imports críticos incluídos",
        "CRITICAL_IMPORTS" in runner_text,
    ),
    (
        "Testes de import graph incluídos",
        "test_platform_import_graph.py" in runner_text
        and "test_session_import_graph.py" in runner_text,
    ),
    (
        "Roadmap 23 final incluída",
        "validate_48v2_roadmap23_final.py" in runner_text,
    ),
    (
        "Contrato público incluído",
        "validate_49_roadmap24_public_contract.py" in runner_text,
    ),
    (
        "Smoke pós-limpeza incluído",
        "validate_50f_v4_roadmap24_smoke_after_cleanup.py" in runner_text,
    ),
    (
        "Guardrails opcionais suportados",
        "--guardrails" in runner_text,
    ),
    (
        "Docs explicam quick",
        "--profile quick" in docs_text,
    ),
    (
        "Docs explicam full",
        "--profile full" in docs_text,
    ),
)


print("=" * 108)
print("#51A / ROADMAP 24.4 - CONTRATO DA SUÍTE OFICIAL")
print("=" * 108)


passed = 0

for index, (
    label,
    ok,
) in enumerate(
    extended,
    1,
):
    passed += int(
        ok
    )

    print(
        f"[{index:02d}] "
        f"{label:<76} "
        f"{'OK' if ok else 'ERRO'}"
    )


print("-" * 108)
print(
    f"PASSARAM: "
    f"{passed}/{len(extended)}"
)


if passed != len(
    extended
):
    raise SystemExit(
        1
    )


print(
    "#51A ROADMAP 24.4: "
    "CONTRATO VALIDADO"
)
