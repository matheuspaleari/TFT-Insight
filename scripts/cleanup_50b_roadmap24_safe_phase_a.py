from __future__ import annotations

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]


SAFE_FILES = (
    ROOT / "estrutura.txt",
    ROOT / "estrutura_tft_insight.txt",
    ROOT / "assets/architecture.png",
    ROOT / "assets/dashboard.png",
    ROOT / "notebooks/01_exploratory_analysis.ipynb",
    ROOT / "tests/test_metrics.py",
    ROOT / "tests/test_transform.py",
)


removed_files = 0
removed_dirs = 0


# Somente lixo gerado automaticamente.
for directory in list(
    ROOT.rglob("__pycache__")
):
    if directory.is_dir():
        shutil.rmtree(
            directory
        )
        removed_dirs += 1


for file in list(
    ROOT.rglob("*.pyc")
):
    if file.is_file():
        file.unlink()
        removed_files += 1


pytest_cache = (
    ROOT
    / "sdk/python/.pytest_cache"
)

if pytest_cache.exists():
    shutil.rmtree(
        pytest_cache
    )
    removed_dirs += 1


# Somente placeholders/listagens já auditados.
for file in SAFE_FILES:
    if (
        file.exists()
        and file.is_file()
    ):
        file.unlink()
        removed_files += 1


print("=" * 108)
print("#50B / ROADMAP 24.3 - LIMPEZA SEGURA FASE A")
print("=" * 108)

print(
    f"Diretórios removidos : {removed_dirs}"
)
print(
    f"Arquivos removidos   : {removed_files}"
)

print()
print(
    "README.md, src/, data/, docs/ e scripts históricos "
    "NÃO foram removidos."
)

print(
    "#50B ROADMAP 24.3: LIMPEZA SEGURA FASE A CONCLUÍDA"
)
