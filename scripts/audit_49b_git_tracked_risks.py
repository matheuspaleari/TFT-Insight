from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


SENSITIVE_PREFIXES = (
    ".env",
    ".streamlit/secrets.toml",
    "data/cache/",
    "data/debug/",
    "data/diagnostics/",
    "data/history/",
    "data/players/",
    "data/knowledge/",
    "data/partner/",
    "data/raw/",
)


def run_git(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout.strip()


code, inside = run_git(
    "rev-parse",
    "--is-inside-work-tree",
)


print("=" * 108)
print("#49B / ROADMAP 24.2 - AUDITORIA DO QUE JÁ ESTÁ VERSIONADO")
print("=" * 108)


if code != 0 or inside.lower() != "true":
    print(
        "INFO: esta pasta ainda não é um repositório Git."
    )
    print(
        "O .gitignore está pronto; não há histórico Git local para auditar."
    )
    raise SystemExit(0)


code, tracked = run_git(
    "ls-files"
)


if code != 0:
    raise SystemExit(
        "ERRO: não foi possível consultar git ls-files"
    )


tracked_files = [
    line.strip().replace("\\", "/")
    for line in tracked.splitlines()
    if line.strip()
]


risks = []


for item in tracked_files:
    if item == ".env":
        risks.append(item)
        continue

    if any(
        item.startswith(prefix)
        for prefix in SENSITIVE_PREFIXES
        if prefix.endswith("/")
    ):
        risks.append(item)

    if item == ".streamlit/secrets.toml":
        risks.append(item)


if risks:
    print(
        "REVISAR: arquivos locais/runtime já estão rastreados pelo Git:"
    )

    for item in risks:
        print(
            f"- {item}"
        )

    print()
    print(
        "IMPORTANTE: adicionar uma regra ao .gitignore não remove "
        "arquivos que já estavam versionados."
    )

    raise SystemExit(1)


print(
    "OK: nenhum arquivo local/runtime sensível auditado "
    "está rastreado pelo Git."
)
