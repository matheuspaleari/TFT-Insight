from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

BLOCK = []
REVIEW = []
OK = []

def add(bucket, label, detail=""):
    bucket.append((label, detail))

# Secrets / local config
env = ROOT / ".env"
if env.exists():
    add(BLOCK, ".env presente na árvore de trabalho", "Arquivo local com configuração/credenciais; não deve entrar no commit.")
else:
    add(OK, ".env ausente da árvore auditada")

# Runtime/cache artifacts: can exist locally, but must be ignored.
runtime_paths = [
    "data/cache", "data/debug", "data/diagnostics", "data/history",
    "data/players", "database",
]
for rel in runtime_paths:
    p = ROOT / rel
    if p.exists():
        add(REVIEW, f"Runtime local presente: {rel}", "Pode permanecer localmente, mas confirme que está ignorado e não staged.")

pycache = list(ROOT.rglob("__pycache__"))
pyc = list(ROOT.rglob("*.pyc"))
if pycache or pyc:
    add(REVIEW, "Caches Python presentes", f"__pycache__={len(pycache)}; pyc={len(pyc)}. Devem ficar fora do Git.")
else:
    add(OK, "Sem caches Python")

# Gitignore contract
gi = ROOT / ".gitignore"
gitignore = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
required_ignore = (
    ".env", "__pycache__/", "*.py[cod]", "data/cache/", "data/diagnostics/",
    "data/history/", "database/*.db", "data/processed/*", "data/raw/*",
)
missing = [x for x in required_ignore if x not in gitignore]
if missing:
    add(BLOCK, ".gitignore incompleto", ", ".join(missing))
else:
    add(OK, ".gitignore cobre segredos/runtime principais")

# Real-looking Riot keys anywhere except .env are a blocker.
riot = re.compile(r"RGAPI-[A-Za-z0-9_-]{30,}")
secret_hits = []
for p in ROOT.rglob("*"):
    if not p.is_file() or p == env:
        continue
    if p.suffix.lower() not in {".py",".md",".txt",".json",".toml",".yaml",".yml",".example"} and p.name != "secrets.toml.example":
        continue
    try:
        text=p.read_text(encoding="utf-8",errors="ignore")
    except Exception:
        continue
    for m in riot.finditer(text):
        value=m.group(0)
        # Documentation placeholders are allowed.
        if "SUA" not in value.upper() and "EXAMPLE" not in value.upper():
            secret_hits.append(str(p.relative_to(ROOT)))
            break
if secret_hits:
    add(BLOCK, "Possíveis Riot API keys fora do .env", ", ".join(secret_hits[:10]))
else:
    add(OK, "Nenhuma Riot API key real detectada fora do .env")

# Portfolio docs expected.
for rel in ("README.md","docs/ARCHITECTURE.md","docs/SETUP.md","docs/VALIDATION.md"):
    if (ROOT/rel).exists():
        add(OK, f"Documento público presente: {rel}")
    else:
        add(BLOCK, f"Documento público ausente: {rel}")

# Archived legacy is intentional, but public-repo decision remains.
archive = ROOT/"scripts/archive/roadmap_legacy"
if archive.exists():
    count=len(list(archive.rglob("*.py")))
    add(REVIEW, "Legado arquivado ainda presente", f"{count} scripts em scripts/archive/roadmap_legacy. Decidir se deve entrar no GitHub.")
else:
    add(OK, "Sem archive legado na árvore")

# Root clutter candidates: audit only, never delete.
root_candidates = (
    "SDK_INSTALL_README.md","SPRINT_2_README.md","WEB_SETUP.md",
    "UPGRADE_v0.4.1A1.md","UPGRADE_v0.5.0-alpha.1.md",
    "UPGRADE_v0.5.0-alpha.1r1.md","UPGRADE_v0.5.0-alpha.2.md",
    "UPGRADE_v0.5.0-alpha.3.md","CLEANUP_MANIFEST.md",
    "inspect_challenger.py","inspect_match.py",
    "test_analysis_dataset.py","test_benchmark.py","test_benchmark_collector.py",
    "test_database.py","test_general_metrics.py","test_metric_evaluator.py",
)
present=[x for x in root_candidates if (ROOT/x).exists()]
if present:
    add(REVIEW, "Arquivos candidatos a organização na raiz", f"{len(present)} itens: " + ", ".join(present))
else:
    add(OK, "Raiz sem candidatos conhecidos de organização")

# Large runtime/public assets.
large=[]
for p in ROOT.rglob("*"):
    if p.is_file() and p.stat().st_size >= 5*1024*1024:
        large.append((p.stat().st_size, str(p.relative_to(ROOT))))
if large:
    add(REVIEW, "Arquivos >= 5 MiB", "; ".join(f"{rel} ({size/1024/1024:.1f} MiB)" for size,rel in sorted(large,reverse=True)))
else:
    add(OK, "Sem arquivos >= 5 MiB")

print("="*116)
print("#55 / ROADMAP 24.8 - GITHUB / PORTFÓLIO READINESS")
print("="*116)

for title,bucket in (("BLOQUEAR",BLOCK),("REVISAR",REVIEW),("OK",OK)):
    print(f"\n{title} ({len(bucket)})")
    print("-"*116)
    if not bucket:
        print("nenhum")
    for label,detail in bucket:
        print(f"- {label}")
        if detail:
            print(f"  {detail}")

print("\n"+"="*116)
print(f"RESUMO: BLOQUEAR={len(BLOCK)} | REVISAR={len(REVIEW)} | OK={len(OK)}")
if BLOCK:
    print("#55 ROADMAP 24.8: BLOQUEADO PARA COMMIT — CORRIGIR ITENS CRÍTICOS")
    raise SystemExit(2)
if REVIEW:
    print("#55 ROADMAP 24.8: REVISAR ANTES DO COMMIT")
    raise SystemExit(1)
print("#55 ROADMAP 24.8: PRONTO PARA AUDITORIA FINAL PRÉ-COMMIT")
