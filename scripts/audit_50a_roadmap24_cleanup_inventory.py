from __future__ import annotations

from pathlib import Path
import hashlib


ROOT = Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


all_files = [
    path
    for path in ROOT.rglob("*")
    if path.is_file()
]


py_files = [
    path
    for path in all_files
    if path.suffix == ".py"
]


pycache_dirs = [
    path
    for path in ROOT.rglob("__pycache__")
    if path.is_dir()
]


pyc_files = [
    path
    for path in ROOT.rglob("*.pyc")
    if path.is_file()
]


empty_files = [
    path
    for path in all_files
    if path.stat().st_size == 0
]


hashes: dict[str, list[Path]] = {}

for path in py_files:
    data = path.read_bytes()

    if not data:
        continue

    digest = hashlib.sha256(
        data
    ).hexdigest()

    hashes.setdefault(
        digest,
        [],
    ).append(
        path
    )


duplicate_groups = [
    paths
    for paths in hashes.values()
    if len(paths) > 1
]


print("=" * 110)
print("#50A / ROADMAP 24.3 - INVENTÁRIO DE LIMPEZA SEGURA")
print("=" * 110)

print(
    f"Arquivos totais       : {len(all_files)}"
)
print(
    f"Arquivos Python       : {len(py_files)}"
)
print(
    f"Diretórios __pycache__: {len(pycache_dirs)}"
)
print(
    f"Arquivos .pyc         : {len(pyc_files)}"
)
print(
    f"Arquivos vazios       : {len(empty_files)}"
)
print(
    f"Grupos Python idênticos: {len(duplicate_groups)}"
)

print()
print("ARQUIVOS VAZIOS")
print("-" * 110)

for path in empty_files:
    print(
        f"- {rel(path)}"
    )


print()
print("DUPLICIDADES PYTHON EXATAS")
print("-" * 110)

for index, group in enumerate(
    duplicate_groups,
    1,
):
    print(
        f"[{index:02d}]"
    )

    for path in group:
        print(
            f"  - {rel(path)}"
        )


print()
print(
    "#50A ROADMAP 24.3: "
    "INVENTÁRIO CONCLUÍDO — NENHUM ARQUIVO FOI ALTERADO"
)
