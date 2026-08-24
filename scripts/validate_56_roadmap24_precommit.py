from __future__ import annotations

from pathlib import Path
import re
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


checks: list[tuple[str, bool, str]] = []


# -----------------------------------------------------------------------------
# 1. Repositório correto
# -----------------------------------------------------------------------------
code, inside = git("rev-parse", "--is-inside-work-tree")
checks.append((
    "Executando dentro de repositório Git",
    code == 0 and inside.lower() == "true",
    inside if code == 0 else "git rev-parse falhou",
))

code, remote = git("remote", "get-url", "origin")
checks.append((
    "Origin aponta para TFT-Insight",
    code == 0 and "matheuspaleari/TFT-Insight" in remote.replace("\\", "/"),
    remote,
))

code, branch = git("branch", "--show-current")
checks.append((
    "Branch atual é main",
    code == 0 and branch == "main",
    branch,
))


# -----------------------------------------------------------------------------
# 2. Nada staged antes da revisão final
# -----------------------------------------------------------------------------
code, staged = git("diff", "--cached", "--name-only")
checks.append((
    "Nada staged antes do git add final",
    code == 0 and not staged.strip(),
    staged,
))


# -----------------------------------------------------------------------------
# 3. Segredos e runtime
# -----------------------------------------------------------------------------
code, tracked = git("ls-files")
tracked_files = {
    line.strip().replace("\\", "/")
    for line in tracked.splitlines()
    if line.strip()
} if code == 0 else set()

sensitive_exact = {
    ".env",
    ".streamlit/secrets.toml",
}

bad_tracked = sorted(
    item
    for item in tracked_files
    if (
        item in sensitive_exact
        or item.endswith(".pyc")
        or "__pycache__/" in item
        or item.startswith("data/cache/")
        or item.startswith("data/debug/")
        or item.startswith("data/diagnostics/")
        or item.startswith("data/history/")
        or item.startswith("data/players/")
        or item.startswith("database/")
        or item.startswith("scripts/archive/")
    )
)

checks.append((
    "Nenhum segredo/runtime/archive já rastreado",
    not bad_tracked,
    ", ".join(bad_tracked[:20]),
))


for candidate in (
    ".env",
    "data/history/matches.jsonl",
    "data/cache/performance/teste.json",
    "data/raw/exemplo.json",
    "data/processed/matches.csv",
):
    code, output = git("check-ignore", "-v", candidate)
    checks.append((
        f"Git ignora: {candidate}",
        code == 0,
        output,
    ))


# -----------------------------------------------------------------------------
# 4. Documentação pública obrigatória
# -----------------------------------------------------------------------------
for relative in (
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/SETUP.md",
    "docs/VALIDATION.md",
    "assets/readme/home.png",
    "assets/readme/analysis.png",
):
    path = ROOT / relative
    checks.append((
        f"Artefato público presente: {relative}",
        path.exists() and (not path.is_file() or path.stat().st_size > 0),
        "",
    ))


# -----------------------------------------------------------------------------
# 5. Legado antigo não deve reaparecer na versão pública atual
# -----------------------------------------------------------------------------
forbidden_paths = (
    "app",
    "ARCHITECTURE.md",
    "INSTRUCOES.md",
    "WEB_SETUP.md",
    "assets/architecture.png",
    "assets/dashboard.png",
    "inspect_match.py",
    "test_database.py",
    "test_general_metrics.py",
    "scripts/archive",
)

for relative in forbidden_paths:
    checks.append((
        f"Legado removido da árvore pública: {relative}",
        not (ROOT / relative).exists(),
        "",
    ))


# -----------------------------------------------------------------------------
# 6. Entrypoints atuais
# -----------------------------------------------------------------------------
for relative in (
    "run_api.py",
    "scripts/run_partner_platform.py",
    "partner_platform/app.py",
    "scripts/validate_51_roadmap24_official_suite.py",
):
    checks.append((
        f"Entrypoint/validador atual presente: {relative}",
        (ROOT / relative).exists(),
        "",
    ))


# -----------------------------------------------------------------------------
# 7. Scan simples de segredos em arquivos que poderiam entrar no commit
# -----------------------------------------------------------------------------
# Inclui arquivos modificados + novos não ignorados.
code, modified = git("diff", "--name-only")
modified_files = {
    line.strip().replace("\\", "/")
    for line in modified.splitlines()
    if line.strip()
} if code == 0 else set()

code, untracked = git(
    "ls-files",
    "--others",
    "--exclude-standard",
)
untracked_files = {
    line.strip().replace("\\", "/")
    for line in untracked.splitlines()
    if line.strip()
} if code == 0 else set()

candidate_files = sorted(modified_files | untracked_files)

secret_patterns = (
    re.compile(r"RGAPI-[A-Za-z0-9_-]{20,}"),
    re.compile(
        r"(?i)(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"
    ),
)

allowed_placeholders = (
    "sua_chave_aqui",
    "your_api_key",
    "example",
    "placeholder",
)

secret_hits: list[str] = []

for relative in candidate_files:
    path = ROOT / relative

    if not path.is_file():
        continue

    if path.suffix.lower() not in {
        ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".example"
    } and path.name != ".env.example":
        continue

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        continue

    lowered = text.lower()

    for pattern in secret_patterns:
        for match in pattern.finditer(text):
            sample = match.group(0).lower()

            if any(
                placeholder in sample
                for placeholder in allowed_placeholders
            ):
                continue

            # Variáveis documentadas sem valor real não bloqueiam.
            if "tft_insight_local_ai_model=llama3.2:3b" in sample:
                continue
            if "tft_insight_ollama_url=http://localhost:11434" in sample:
                continue

            secret_hits.append(relative)
            break

        if relative in secret_hits:
            break


checks.append((
    "Nenhum possível segredo detectado nas mudanças",
    not secret_hits,
    ", ".join(sorted(set(secret_hits))[:20]),
))


# -----------------------------------------------------------------------------
# 8. Arquivos grandes que podem entrar no commit
# -----------------------------------------------------------------------------
large_candidates: list[str] = []

for relative in candidate_files:
    path = ROOT / relative

    if not path.is_file():
        continue

    size = path.stat().st_size

    if size >= 20 * 1024 * 1024:
        large_candidates.append(
            f"{relative} ({size / 1024 / 1024:.1f} MiB)"
        )

checks.append((
    "Nenhum arquivo candidato >= 20 MiB",
    not large_candidates,
    "; ".join(large_candidates),
))


# -----------------------------------------------------------------------------
# 9. Mudanças existem e são revisáveis
# -----------------------------------------------------------------------------
code, status = git("status", "--short")

status_lines = [
    line
    for line in status.splitlines()
    if line.strip()
] if code == 0 else []

checks.append((
    "Existem mudanças para o novo release",
    bool(status_lines),
    f"{len(status_lines)} entrada(s) no git status",
))

checks.append((
    "Quantidade de mudanças não é vazia",
    len(candidate_files) > 0,
    f"{len(candidate_files)} arquivo(s) modificados/novos não ignorados",
))


# -----------------------------------------------------------------------------
# Saída
# -----------------------------------------------------------------------------
print("=" * 118)
print("#56 / ROADMAP 24.9 - AUDITORIA FINAL PRÉ-COMMIT")
print("=" * 118)

passed = 0

for index, (label, ok, detail) in enumerate(checks, 1):
    passed += int(ok)

    print(
        f"[{index:02d}] "
        f"{label:<86} "
        f"{'OK' if ok else 'ERRO'}"
    )

    if not ok and detail:
        print(f"     {detail[:1400]}")


print("-" * 118)
print(f"PASSARAM: {passed}/{len(checks)}")


print()
print("RESUMO DAS MUDANÇAS")
print("-" * 118)
print(f"Modificados/deletados : {len(modified_files)}")
print(f"Novos não ignorados   : {len(untracked_files)}")
print(f"Candidatos ao commit  : {len(candidate_files)}")


if passed != len(checks):
    print()
    print("#56 ROADMAP 24.9: BLOQUEADO — NÃO EXECUTE git add")
    raise SystemExit(1)


print()
print("#56 ROADMAP 24.9: PRONTO PARA STAGE CONTROLADO")
print("Nenhum arquivo foi staged, commitado ou enviado por esta auditoria.")
