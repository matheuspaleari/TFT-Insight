from __future__ import annotations

import argparse
import ast
import importlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CheckResult:
    label: str
    ok: bool
    detail: str = ""


CRITICAL_FILES = (
    "run_api.py",
    "partner_platform/app.py",
    "partner_platform/pages/home_page.py",
    "partner_platform/pages/benchmark_page.py",
    "partner_platform/platform_core/context.py",
    "partner_platform/platform_core/router.py",
    "partner_platform/navigation/catalog.py",
    "src/integration_engine/api/app.py",
)


CRITICAL_IMPORTS = (
    "partner_platform.platform_core.context",
    "partner_platform.platform_core.router",
    "partner_platform.navigation.catalog",
    "partner_platform.pages.home_page",
    "partner_platform.pages.benchmark_page",
    "src.integration_engine.api.app",
)


QUICK_SCRIPTS = (
    "scripts/test_platform_imports.py",
    "scripts/test_platform_import_graph.py",
    "scripts/test_session_import_graph.py",
)


FULL_SCRIPTS = (
    "scripts/validate_48v2_roadmap23_final.py",
    "scripts/validate_49_roadmap24_public_contract.py",
    "scripts/validate_50f_v4_roadmap24_smoke_after_cleanup.py",
)


OPTIONAL_GUARDRAIL_SCRIPTS = (
    "scripts/audit_31_general_guardrails.py",
)


def _run_script(relative: str) -> CheckResult:
    path = ROOT / relative

    if not path.exists():
        return CheckResult(
            label=f"Executa: {relative}",
            ok=False,
            detail="arquivo ausente",
        )

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )

    output = (
        result.stderr.strip()
        or result.stdout.strip()
    )

    return CheckResult(
        label=f"Executa: {relative}",
        ok=result.returncode == 0,
        detail=output[-1200:],
    )


def _check_files() -> list[CheckResult]:
    return [
        CheckResult(
            label=f"Arquivo crítico: {relative}",
            ok=(ROOT / relative).exists(),
        )
        for relative in CRITICAL_FILES
    ]


def _check_syntax() -> CheckResult:
    errors: list[str] = []
    count = 0

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
            count += 1
        except Exception as error:
            errors.append(
                f"{path.relative_to(ROOT)}: {error}"
            )

    return CheckResult(
        label=f"Sintaxe Python ({count} arquivos)",
        ok=not errors,
        detail="; ".join(errors[:6]),
    )


def _check_imports() -> list[CheckResult]:
    sys.path.insert(
        0,
        str(ROOT),
    )

    results: list[CheckResult] = []

    for module_name in CRITICAL_IMPORTS:
        try:
            importlib.import_module(
                module_name
            )
            results.append(
                CheckResult(
                    label=f"Import: {module_name}",
                    ok=True,
                )
            )
        except Exception as error:
            results.append(
                CheckResult(
                    label=f"Import: {module_name}",
                    ok=False,
                    detail=repr(error),
                )
            )

    return results


def _print_results(
    title: str,
    results: list[CheckResult],
) -> bool:
    print("=" * 116)
    print(title)
    print("=" * 116)

    passed = 0

    for index, result in enumerate(
        results,
        1,
    ):
        passed += int(
            result.ok
        )

        print(
            f"[{index:02d}] "
            f"{result.label:<84} "
            f"{'OK' if result.ok else 'ERRO'}"
        )

        if (
            not result.ok
            and result.detail
        ):
            print(
                f"     {result.detail}"
            )

    print("-" * 116)
    print(
        f"PASSARAM: "
        f"{passed}/{len(results)}"
    )

    return passed == len(
        results
    )


def run_quick() -> bool:
    results: list[CheckResult] = []

    results.extend(
        _check_files()
    )

    results.append(
        _check_syntax()
    )

    results.extend(
        _check_imports()
    )

    results.extend(
        _run_script(script)
        for script in QUICK_SCRIPTS
    )

    return _print_results(
        "#51 / ROADMAP 24.4 - SUÍTE OFICIAL / QUICK",
        results,
    )


def run_full(
    include_guardrails: bool,
) -> bool:
    results: list[CheckResult] = []

    # O perfil full começa pela base quick.
    quick_ok = run_quick()

    results.append(
        CheckResult(
            label="Perfil QUICK",
            ok=quick_ok,
        )
    )

    for script in FULL_SCRIPTS:
        results.append(
            _run_script(
                script
            )
        )

    if include_guardrails:
        for script in OPTIONAL_GUARDRAIL_SCRIPTS:
            path = ROOT / script

            if not path.exists():
                results.append(
                    CheckResult(
                        label=f"Guardrail opcional: {script}",
                        ok=True,
                        detail="ausente — ignorado",
                    )
                )
                continue

            results.append(
                _run_script(
                    script
                )
            )

    return _print_results(
        "#51 / ROADMAP 24.4 - SUÍTE OFICIAL / FULL",
        results,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Suíte oficial de validação do TFT Insight."
        )
    )

    parser.add_argument(
        "--profile",
        choices=(
            "quick",
            "full",
        ),
        default="quick",
        help=(
            "quick = sanidade local; "
            "full = contratos + smoke pós-limpeza."
        ),
    )

    parser.add_argument(
        "--guardrails",
        action="store_true",
        help=(
            "No perfil full, inclui auditoria geral "
            "de guardrails quando disponível."
        ),
    )

    args = parser.parse_args()

    if args.profile == "quick":
        ok = run_quick()
    else:
        ok = run_full(
            include_guardrails=args.guardrails,
        )

    if ok:
        print()
        print(
            "#51 ROADMAP 24.4: "
            "SUÍTE OFICIAL VALIDADA"
        )
        return 0

    print()
    print(
        "#51 ROADMAP 24.4: REVISAR"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
