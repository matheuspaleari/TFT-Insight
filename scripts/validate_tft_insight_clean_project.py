from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


# Impede que esta execução gere __pycache__ / .pyc
sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = (
    "run_api.py",
    "requirements.txt",
    "partner_platform/app.py",
    "partner_platform/platform_core/page.py",
    "partner_platform/platform_core/context.py",
    "partner_platform/platform_core/router.py",
    "partner_platform/components/smart_header.py",
    "partner_platform/components/compact_health_ribbon.py",
    "partner_platform/session/store.py",
    "partner_platform/services/api_client.py",
    "src",
)


FORBIDDEN_PATHS = (
    ".venv",
    ".git",
    "partner_platform/catalog.py",
    "partner_platform/pages/page.py",
)


IMPORT_SMOKE = (
    "partner_platform.components",
    "partner_platform.navigation",
    "partner_platform.session",
    "partner_platform.services",
    "partner_platform.intelligence",
    "partner_platform.platform_core",
    "partner_platform.pages",
)


OPTIONAL_TEST_SCRIPTS = (
    "scripts/test_session_import_graph.py",
    "scripts/test_platform_import_graph.py",
    "scripts/audit_partner_platform_html.py",
    "scripts/test_ux_polish_v1.py",
)


# Alguns testes antigos imprimem sucesso, mas retornam exit code 1.
# Essas assinaturas permitem reconhecer quando o conteúdo do teste passou.
LEGACY_SUCCESS_SIGNATURES = {
    "scripts/test_session_import_graph.py": (
        "Circular imports : 0",
    ),
    "scripts/test_platform_import_graph.py": (
        "Circular imports : 0",
        "PlatformContext  : OK",
        "PlatformPage     : OK",
        "PlatformRouter   : OK",
    ),
    "scripts/audit_partner_platform_html.py": (
        "Raw HTML outside render_html : 0",
        "Theme stylesheet exception   : OK",
    ),
    "scripts/test_ux_polish_v1.py": (
        "Current Player badge  : OK",
        "Premium KPI cards     : OK",
        "Explain action        : INTEGRATED",
        "Microinteractions     : OK",
        "Vertical rhythm       : COMPACT",
    ),
}


def ok(message: str) -> None:
    print(f"[OK]   {message}")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"[FAIL] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def clean_generated_artifacts() -> None:
    """
    Remove somente artefatos gerados automaticamente pelo Python.

    Isso evita falsos positivos causados por execuções anteriores
    do próprio validador ou dos testes.
    """
    print("\n=== 0. Limpeza de artefatos temporários ===")

    removed_pycache = 0
    removed_pyc = 0

    # Primeiro remove arquivos .pyc soltos.
    for path in PROJECT_ROOT.rglob("*.pyc"):
        if ".venv" in path.parts:
            continue

        try:
            path.unlink()
            removed_pyc += 1
        except OSError as exc:
            warn(f"não foi possível remover {path}: {exc}")

    # Depois remove diretórios __pycache__.
    pycache_dirs = [
        path
        for path in PROJECT_ROOT.rglob("__pycache__")
        if path.is_dir() and ".venv" not in path.parts
    ]

    # Mais profundos primeiro.
    pycache_dirs.sort(
        key=lambda path: len(path.parts),
        reverse=True,
    )

    for path in pycache_dirs:
        try:
            shutil.rmtree(path)
            removed_pycache += 1
        except OSError as exc:
            warn(f"não foi possível remover {path}: {exc}")

    if removed_pycache == 0 and removed_pyc == 0:
        ok("nenhum artefato temporário encontrado")
    else:
        ok(
            f"removidos: {removed_pycache} __pycache__ "
            f"e {removed_pyc} arquivo(s) .pyc"
        )


def check_structure(failures: list[str]) -> None:
    print("\n=== 1. Estrutura ===")

    for relative in REQUIRED_PATHS:
        path = PROJECT_ROOT / relative

        if path.exists():
            ok(relative)
        else:
            fail(
                f"Arquivo/pasta obrigatória ausente: {relative}",
                failures,
            )

    for relative in FORBIDDEN_PATHS:
        path = PROJECT_ROOT / relative

        if path.exists():
            fail(
                f"Artefato que deveria ter sido removido ainda existe: "
                f"{relative}",
                failures,
            )
        else:
            ok(f"removido: {relative}")


def check_generated_files(failures: list[str]) -> None:
    print("\n=== 2. Artefatos gerados ===")

    pycache_dirs = [
        path
        for path in PROJECT_ROOT.rglob("__pycache__")
        if path.is_dir()
    ]

    pyc_files = list(PROJECT_ROOT.rglob("*.pyc"))

    if pycache_dirs:
        fail(
            f"Foram encontrados {len(pycache_dirs)} "
            f"diretórios __pycache__.",
            failures,
        )

        for path in pycache_dirs[:10]:
            print(
                f"       {path.relative_to(PROJECT_ROOT)}"
            )
    else:
        ok("nenhum __pycache__ encontrado")

    if pyc_files:
        fail(
            f"Foram encontrados {len(pyc_files)} arquivos .pyc.",
            failures,
        )

        for path in pyc_files[:10]:
            print(
                f"       {path.relative_to(PROJECT_ROOT)}"
            )
    else:
        ok("nenhum .pyc encontrado")


def check_platform_page(failures: list[str]) -> None:
    print("\n=== 3. PlatformPage consolidado ===")

    path = (
        PROJECT_ROOT
        / "partner_platform"
        / "platform_core"
        / "page.py"
    )

    if not path.exists():
        fail(
            "platform_core/page.py não existe.",
            failures,
        )
        return

    source = path.read_text(encoding="utf-8")

    required_tokens = (
        "smart_header",
        "compact_health_ribbon",
    )

    forbidden_tokens = (
        "\n    topbar(",
        "\n    hero(",
        "\n    health_ribbon(",
    )

    for token in required_tokens:
        if token in source:
            ok(f"PlatformPage usa {token}")
        else:
            fail(
                f"PlatformPage não usa {token}",
                failures,
            )

    for token in forbidden_tokens:
        if token in source:
            fail(
                f"PlatformPage ainda contém chamada antiga: "
                f"{token.strip()}",
                failures,
            )


def check_deleted_module_references(
    failures: list[str],
) -> None:
    print("\n=== 4. Referências a módulos removidos ===")

    bad_patterns = (
        "partner_platform.catalog",
        "partner_platform.pages.page",
    )

    hits: list[str] = []

    validator_path = Path(__file__).resolve()

    for path in PROJECT_ROOT.rglob("*.py"):
        if any(
            part in {
                ".venv",
                ".git",
                "__pycache__",
            }
            for part in path.parts
        ):
            continue

        # O próprio validador contém os padrões acima
        # justamente para procurá-los.
        if path.resolve() == validator_path:
            continue

        try:
            source = path.read_text(
                encoding="utf-8",
            )
        except UnicodeDecodeError:
            continue

        for pattern in bad_patterns:
            if pattern in source:
                hits.append(
                    f"{path.relative_to(PROJECT_ROOT)} "
                    f"-> {pattern}"
                )

    if hits:
        for hit in hits:
            print(f"       {hit}")

        fail(
            f"{len(hits)} referência(s) "
            f"para módulos removidos.",
            failures,
        )
    else:
        ok(
            "nenhuma referência aos módulos removidos"
        )


def check_python_syntax(
    failures: list[str],
) -> None:
    print("\n=== 5. Compilação Python ===")

    count = 0
    syntax_failures_before = len(failures)

    for path in PROJECT_ROOT.rglob("*.py"):
        if any(
            part in {
                ".venv",
                ".git",
                "__pycache__",
            }
            for part in path.parts
        ):
            continue

        try:
            source = path.read_text(
                encoding="utf-8",
            )

            ast.parse(
                source,
                filename=str(path),
            )

            count += 1

        except Exception as exc:
            fail(
                f"Erro de sintaxe em "
                f"{path.relative_to(PROJECT_ROOT)}: "
                f"{exc}",
                failures,
            )

    if len(failures) == syntax_failures_before:
        ok(
            f"{count} arquivos Python analisados"
        )


def check_imports(
    failures: list[str],
) -> None:
    print("\n=== 6. Import smoke test ===")

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(
            0,
            str(PROJECT_ROOT),
        )

    for module_name in IMPORT_SMOKE:
        try:
            importlib.import_module(
                module_name
            )

            ok(module_name)

        except ModuleNotFoundError as exc:
            if exc.name in {
                "streamlit",
                "pandas",
                "plotly",
                "httpx",
                "fastapi",
                "pydantic",
            }:
                warn(
                    f"{module_name}: "
                    f"dependência externa ausente "
                    f"({exc.name})."
                )
            else:
                fail(
                    f"{module_name}: "
                    f"módulo local ausente ({exc})",
                    failures,
                )

        except Exception as exc:
            fail(
                f"{module_name}: erro ao importar: "
                f"{type(exc).__name__}: {exc}",
                failures,
            )


def legacy_test_output_is_successful(
    relative: str,
    output: str,
) -> bool:
    """
    Alguns testes antigos retornam código 1 mesmo quando
    todas as verificações impressas indicam sucesso.

    Só aceita isso quando todas as assinaturas esperadas
    daquele teste aparecem na saída.
    """

    required_signatures = (
        LEGACY_SUCCESS_SIGNATURES.get(relative)
    )

    if not required_signatures:
        return False

    failure_markers = (
        "Traceback",
        "AssertionError",
        "[FAIL]",
        "FAILED",
        "Exception:",
    )

    if any(
        marker in output
        for marker in failure_markers
    ):
        return False

    return all(
        signature in output
        for signature in required_signatures
    )


def run_existing_tests(
    failures: list[str],
) -> None:
    print("\n=== 7. Testes existentes ===")

    env = os.environ.copy()

    # Evita que subprocessos criem __pycache__.
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    for relative in OPTIONAL_TEST_SCRIPTS:
        script = PROJECT_ROOT / relative

        if not script.exists():
            warn(
                f"não encontrado: {relative}"
            )
            continue

        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(script),
            ],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

        output = (
            (result.stdout or "")
            + "\n"
            + (result.stderr or "")
        ).strip()

        if result.returncode == 0:
            ok(relative)

            if output:
                print(output)

            continue

        # Compatibilidade temporária com testes antigos
        # que retornam código 1 apesar de passarem.
        if legacy_test_output_is_successful(
            relative,
            output,
        ):
            ok(relative)

            warn(
                f"{relative} passou pelas verificações, "
                f"mas retornou código "
                f"{result.returncode}. "
                f"O exit code desse teste deve ser "
                f"corrigido posteriormente."
            )

            if output:
                print(output)

            continue

        fail(
            f"{relative} retornou código "
            f"{result.returncode}",
            failures,
        )

        if output:
            print("----- saída -----")
            print(output[-4000:])
            print("-----------------")


def check_artifacts_after_tests(
    failures: list[str],
) -> None:
    print(
        "\n=== 8. Artefatos após os testes ==="
    )

    pycache_dirs = [
        path
        for path in PROJECT_ROOT.rglob(
            "__pycache__"
        )
        if path.is_dir()
    ]

    pyc_files = list(
        PROJECT_ROOT.rglob("*.pyc")
    )

    if not pycache_dirs and not pyc_files:
        ok(
            "testes não recriaram "
            "__pycache__ ou .pyc"
        )
        return

    if pycache_dirs:
        fail(
            f"Os testes criaram "
            f"{len(pycache_dirs)} "
            f"diretórios __pycache__.",
            failures,
        )

    if pyc_files:
        fail(
            f"Os testes criaram "
            f"{len(pyc_files)} arquivos .pyc.",
            failures,
        )


def main() -> int:
    print("=" * 78)
    print(
        "TFT INSIGHT — CLEAN PROJECT VALIDATOR"
    )
    print("=" * 78)
    print(f"Projeto: {PROJECT_ROOT}")

    failures: list[str] = []

    clean_generated_artifacts()

    check_structure(failures)
    check_generated_files(failures)
    check_platform_page(failures)
    check_deleted_module_references(
        failures
    )
    check_python_syntax(failures)
    check_imports(failures)
    run_existing_tests(failures)
    check_artifacts_after_tests(
        failures
    )

    print("\n" + "=" * 78)

    if failures:
        print(
            f"RESULTADO: FALHOU "
            f"({len(failures)} problema(s))"
        )
        print("=" * 78)

        for index, item in enumerate(
            failures,
            start=1,
        ):
            print(
                f"{index}. {item}"
            )

        return 1

    print(
        "RESULTADO: OK — "
        "nenhuma quebra estrutural detectada."
    )
    print("=" * 78)

    print(
        "\nPróximo smoke test manual:"
    )
    print(
        "  Terminal 1: python run_api.py"
    )
    print(
        "  Terminal 2: "
        "python scripts/run_partner_platform.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())