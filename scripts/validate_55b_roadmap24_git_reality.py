from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout.strip()


def norm(value: str) -> str:
    return value.replace("\\", "/")


BLOCK: list[tuple[str, str]] = []
REVIEW: list[tuple[str, str]] = []
OK: list[tuple[str, str]] = []


code, inside = git("rev-parse", "--is-inside-work-tree")

if code != 0 or inside.lower() != "true":
    BLOCK.append((
        "Pasta não é um repositório Git",
        "Execute esta auditoria na raiz real do repositório.",
    ))
else:
    OK.append((
        "Repositório Git detectado",
        "",
    ))


code, tracked_raw = git("ls-files")
tracked = {
    norm(line.strip())
    for line in tracked_raw.splitlines()
    if line.strip()
} if code == 0 else set()


code, staged_raw = git(
    "diff",
    "--cached",
    "--name-only",
)
staged = {
    norm(line.strip())
    for line in staged_raw.splitlines()
    if line.strip()
} if code == 0 else set()


SENSITIVE_EXACT = {
    ".env",
    ".streamlit/secrets.toml",
}

RUNTIME_PREFIXES = (
    "data/cache/",
    "data/debug/",
    "data/diagnostics/",
    "data/history/",
    "data/players/",
)

RUNTIME_PATTERNS = (
    "database/",
    "__pycache__/",
)


for sensitive in sorted(SENSITIVE_EXACT):
    path = ROOT / sensitive

    if sensitive in tracked:
        BLOCK.append((
            f"Arquivo sensível rastreado: {sensitive}",
            "O .gitignore não remove arquivos que já estavam versionados.",
        ))
    elif sensitive in staged:
        BLOCK.append((
            f"Arquivo sensível staged: {sensitive}",
            "Retire do stage antes do commit.",
        ))
    elif path.exists():
        code, ignored = git(
            "check-ignore",
            "-q",
            sensitive,
        )

        if code == 0:
            OK.append((
                f"Arquivo local protegido pelo Git: {sensitive}",
                "Existe localmente, mas está ignorado e não rastreado.",
            ))
        else:
            BLOCK.append((
                f"Arquivo local não protegido: {sensitive}",
                "Existe e não está confirmado como ignorado.",
            ))
    else:
        OK.append((
            f"Arquivo sensível ausente: {sensitive}",
            "",
        ))


runtime_tracked = sorted(
    item
    for item in tracked
    if (
        item.endswith(".pyc")
        or "__pycache__/" in item
        or any(
            item.startswith(prefix)
            for prefix in RUNTIME_PREFIXES
        )
        or item.startswith("database/")
    )
)

runtime_staged = sorted(
    item
    for item in staged
    if (
        item.endswith(".pyc")
        or "__pycache__/" in item
        or any(
            item.startswith(prefix)
            for prefix in RUNTIME_PREFIXES
        )
        or item.startswith("database/")
    )
)


if runtime_tracked:
    BLOCK.append((
        "Runtime/cache já rastreado pelo Git",
        ", ".join(runtime_tracked[:20]),
    ))
else:
    OK.append((
        "Nenhum runtime/cache auditado está rastreado",
        "",
    ))


if runtime_staged:
    BLOCK.append((
        "Runtime/cache está staged",
        ", ".join(runtime_staged[:20]),
    ))
else:
    OK.append((
        "Nenhum runtime/cache auditado está staged",
        "",
    ))


ARCHIVE_PREFIX = "scripts/archive/roadmap_legacy/"
archive_tracked = sorted(
    item
    for item in tracked
    if item.startswith(ARCHIVE_PREFIX)
)
archive_staged = sorted(
    item
    for item in staged
    if item.startswith(ARCHIVE_PREFIX)
)

if archive_staged:
    REVIEW.append((
        "Archive legado está no stage",
        f"{len(archive_staged)} arquivo(s). Decidir antes do commit se esse histórico deve ser público.",
    ))
elif archive_tracked:
    REVIEW.append((
        "Archive legado já faz parte do histórico Git",
        f"{len(archive_tracked)} arquivo(s). Decidir se será mantido publicamente.",
    ))
elif (ROOT / "scripts/archive/roadmap_legacy").exists():
    REVIEW.append((
        "Archive legado existe apenas localmente",
        "Não está staged/rastreado nesta auditoria; decidir se deve permanecer fora do Git.",
    ))
else:
    OK.append((
        "Sem archive legado",
        "",
    ))


ROOT_CANDIDATES = (
    "SDK_INSTALL_README.md",
    "SPRINT_2_README.md",
    "WEB_SETUP.md",
    "UPGRADE_v0.4.1A1.md",
    "UPGRADE_v0.5.0-alpha.1.md",
    "UPGRADE_v0.5.0-alpha.1r1.md",
    "UPGRADE_v0.5.0-alpha.2.md",
    "UPGRADE_v0.5.0-alpha.3.md",
    "CLEANUP_MANIFEST.md",
    "inspect_challenger.py",
    "inspect_match.py",
    "test_analysis_dataset.py",
    "test_benchmark.py",
    "test_benchmark_collector.py",
    "test_database.py",
    "test_general_metrics.py",
    "test_metric_evaluator.py",
)

candidate_info = []

for item in ROOT_CANDIDATES:
    path = ROOT / item
    if not path.exists():
        continue

    state = []

    if item in tracked:
        state.append("tracked")

    if item in staged:
        state.append("staged")

    candidate_info.append(
        f"{item} ({'/'.join(state) if state else 'local'})"
    )


if candidate_info:
    REVIEW.append((
        "Arquivos históricos/dev na raiz",
        "; ".join(candidate_info),
    ))
else:
    OK.append((
        "Raiz sem candidatos conhecidos de organização",
        "",
    ))


LARGE_TARGETS = (
    "data/static_data/communitydragon/latest/pt_br.json",
    "data/history/matches.jsonl",
)

for item in LARGE_TARGETS:
    path = ROOT / item

    if not path.exists():
        continue

    size_mib = path.stat().st_size / 1024 / 1024

    if item in staged:
        REVIEW.append((
            f"Arquivo grande staged: {item}",
            f"{size_mib:.1f} MiB",
        ))
    elif item in tracked:
        REVIEW.append((
            f"Arquivo grande rastreado: {item}",
            f"{size_mib:.1f} MiB",
        ))
    else:
        code, _ = git(
            "check-ignore",
            "-q",
            item,
        )

        if code == 0:
            OK.append((
                f"Arquivo grande local ignorado: {item}",
                f"{size_mib:.1f} MiB",
            ))
        else:
            REVIEW.append((
                f"Arquivo grande local não rastreado: {item}",
                f"{size_mib:.1f} MiB; decidir se deve ser versionado.",
            ))


code, status_raw = git(
    "status",
    "--short",
)

if code == 0:
    status_lines = [
        line
        for line in status_raw.splitlines()
        if line.strip()
    ]

    REVIEW.append((
        "Resumo atual do git status",
        (
            f"{len(status_lines)} alteração(ões) detectada(s). "
            "A auditoria final 24.9 revisará o conteúdo antes do git add/commit."
        ),
    ))


print("=" * 118)
print("#55B / ROADMAP 24.8 - AUDITORIA DO ESTADO REAL DO GIT")
print("=" * 118)

for title, bucket in (
    ("BLOQUEAR", BLOCK),
    ("REVISAR", REVIEW),
    ("OK", OK),
):
    print()
    print(f"{title} ({len(bucket)})")
    print("-" * 118)

    if not bucket:
        print("nenhum")

    for label, detail in bucket:
        print(f"- {label}")

        if detail:
            print(f"  {detail}")


print()
print("=" * 118)
print(
    f"RESUMO: BLOQUEAR={len(BLOCK)} | "
    f"REVISAR={len(REVIEW)} | "
    f"OK={len(OK)}"
)


if BLOCK:
    print(
        "#55B ROADMAP 24.8: BLOQUEADO — "
        "HÁ RISCO REAL NO ESTADO DO GIT"
    )
    raise SystemExit(2)


print(
    "#55B ROADMAP 24.8: "
    "SEM BLOQUEIO DE SEGREDO/RUNTIME NO GIT"
)

if REVIEW:
    print(
        "Existem decisões de organização para fechar antes da 24.9."
    )
