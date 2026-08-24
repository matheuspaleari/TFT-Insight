from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


forbidden_existing = (
    ROOT / "estrutura.txt",
    ROOT / "estrutura_tft_insight.txt",
    ROOT / "assets/architecture.png",
    ROOT / "assets/dashboard.png",
    ROOT / "notebooks/01_exploratory_analysis.ipynb",
    ROOT / "tests/test_metrics.py",
    ROOT / "tests/test_transform.py",
)


checks = []


checks.append(
    (
        "Nenhum __pycache__ restante",
        not any(
            path.is_dir()
            for path in ROOT.rglob("__pycache__")
        ),
    )
)


checks.append(
    (
        "Nenhum .pyc restante",
        not any(
            path.is_file()
            for path in ROOT.rglob("*.pyc")
        ),
    )
)


checks.append(
    (
        "pytest cache do SDK removido",
        not (
            ROOT
            / "sdk/python/.pytest_cache"
        ).exists(),
    )
)


for path in forbidden_existing:
    checks.append(
        (
            f"Removido: {path.relative_to(ROOT)}",
            not path.exists(),
        )
    )


checks.extend(
    (
        (
            "README preservado",
            (
                ROOT
                / "README.md"
            ).exists(),
        ),
        (
            "src preservado",
            (
                ROOT
                / "src"
            ).is_dir(),
        ),
        (
            "partner_platform preservado",
            (
                ROOT
                / "partner_platform"
            ).is_dir(),
        ),
        (
            "data preservado",
            (
                ROOT
                / "data"
            ).is_dir(),
        ),
        (
            "docs preservado",
            (
                ROOT
                / "docs"
            ).is_dir(),
        ),
    )
)


syntax_ok = True
syntax_count = 0


for path in ROOT.rglob("*.py"):
    if "__pycache__" in path.parts:
        continue

    try:
        ast.parse(
            path.read_text(
                encoding="utf-8",
                errors="strict",
            ),
            filename=str(path),
        )
        syntax_count += 1

    except Exception as error:
        syntax_ok = False
        print(
            f"SINTAXE ERRO: {path}: {error}"
        )


checks.append(
    (
        f"Sintaxe Python válida ({syntax_count} arquivos)",
        syntax_ok,
    )
)


print("=" * 108)
print("#50C / ROADMAP 24.3 - VALIDAÇÃO PÓS-LIMPEZA FASE A")
print("=" * 108)


passed = 0


for index, (
    label,
    ok,
) in enumerate(
    checks,
    1,
):
    passed += int(
        ok
    )

    print(
        f"[{index:02d}] "
        f"{label:<74} "
        f"{'OK' if ok else 'ERRO'}"
    )


print("-" * 108)
print(
    f"PASSARAM: {passed}/{len(checks)}"
)


if passed != len(checks):
    print(
        "#50C ROADMAP 24.3: REVISAR"
    )
    raise SystemExit(1)


print(
    "#50C ROADMAP 24.3: "
    "LIMPEZA SEGURA FASE A VALIDADA"
)
