from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: list[str]) -> bool:
    print(f"\n[{label}]")
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )
    status = "OK" if result.returncode == 0 else "FALHOU"
    print(f"{label}: {status}")
    return result.returncode == 0


def main() -> None:
    checks = [
        run(
            "Compile",
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                "src/sprint1_engine",
            ],
        ),
        run(
            "Knowledge Database",
            [
                sys.executable,
                "scripts/initialize_sprint1_knowledge.py",
            ],
        ),
        run(
            "Quality & Calibration",
            [
                sys.executable,
                "scripts/test_sprint1_quality.py",
            ],
        ),
    ]

    print("\n" + "=" * 80)
    print("TFT INSIGHT - SPRINT 1 VALIDATION SUITE")
    print("=" * 80)

    if all(checks):
        print("✓ Todos os testes obrigatórios passaram.")
        return

    raise SystemExit("Um ou mais testes falharam.")


if __name__ == "__main__":
    main()
