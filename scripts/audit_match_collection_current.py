from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"

REPORT = ROOT / "match_collection_current_audit.txt"

SEARCH_TERMS = (
    "data/raw",
    "match-v1",
    "match_ids",
    "match_id",
    "get_match",
    "get_matches",
    "riot api",
    "riot_api",
    "tft_set_core_name",
    "game_datetime",
)


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except Exception:
        return str(path)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return None
    except Exception:
        return None


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None


def safe_datetime(value):
    try:
        timestamp = int(value)

        # Riot game_datetime normalmente está em milissegundos.
        if timestamp > 10_000_000_000:
            timestamp /= 1000

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )
    except Exception:
        return None


lines: list[str] = []


def write(value: str = ""):
    lines.append(value)


def section(title: str):
    write()
    write("=" * 120)
    write(title)
    write("=" * 120)


# ======================================================================================
# 1. RAW DATA
# ======================================================================================

section("1. ESTADO ATUAL DE data/raw")

json_files = (
    sorted(RAW_ROOT.rglob("*.json"))
    if RAW_ROOT.exists()
    else []
)

write(f"JSONs encontrados: {len(json_files)}")

sets: dict[str, int] = {}
dated_matches = []

for path in json_files:
    payload = load_json(path)

    if not isinstance(payload, dict):
        continue

    info = payload.get("info")

    if not isinstance(info, dict):
        continue

    set_name = str(
        info.get("tft_set_core_name")
        or "<SEM_SET>"
    )

    sets[set_name] = sets.get(set_name, 0) + 1

    game_datetime = safe_datetime(
        info.get("game_datetime")
    )

    if game_datetime:
        dated_matches.append(
            (
                game_datetime,
                path,
                set_name,
            )
        )

for set_name, count in sorted(
    sets.items(),
    key=lambda item: -item[1],
):
    write(f"{set_name:<30} {count}")


# ======================================================================================
# 2. DATAS
# ======================================================================================

section("2. PARTIDAS MAIS RECENTES LOCALMENTE")

dated_matches.sort(
    key=lambda item: item[0],
    reverse=True,
)

if not dated_matches:
    write("Nenhuma game_datetime válida encontrada.")
else:
    for dt, path, set_name in dated_matches[:30]:
        write(
            f"{dt.isoformat():<32} "
            f"{set_name:<15} "
            f"{relative(path)}"
        )


# ======================================================================================
# 3. CÓDIGO DE COLETA
# ======================================================================================

section("3. ARQUIVOS QUE PODEM COLETAR / SALVAR RIOT MATCH")

matches = []

for path in ROOT.rglob("*.py"):
    rel = relative(path)

    if (
        "/archive/" in f"/{rel}"
        or "__pycache__" in rel
        or path.name == Path(__file__).name
    ):
        continue

    text = read_text(path)

    if text is None:
        continue

    lowered = text.lower()

    score = sum(
        lowered.count(term.lower())
        for term in SEARCH_TERMS
    )

    if score <= 0:
        continue

    hits = []

    for number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        lower_line = line.lower()

        if any(
            term.lower() in lower_line
            for term in SEARCH_TERMS
        ):
            hits.append(
                (
                    number,
                    line.strip(),
                )
            )

    matches.append(
        (
            score,
            path,
            hits[:40],
        )
    )


matches.sort(
    key=lambda item: (
        -item[0],
        relative(item[1]),
    )
)


for score, path, hits in matches[:60]:
    write()
    write("-" * 120)
    write(
        f"{relative(path)} — score={score}"
    )
    write("-" * 120)

    for number, line in hits:
        write(
            f"{number:5d}: {line}"
        )


# ======================================================================================
# 4. CLASSES/FUNÇÕES MAIS RELEVANTES
# ======================================================================================

section("4. FUNÇÕES / CLASSES RELACIONADAS A MATCH / RIOT")

keywords = (
    "match",
    "riot",
    "history",
    "fetch",
    "collect",
    "download",
)

for _, path, _ in matches[:40]:
    text = read_text(path)

    if text is None:
        continue

    try:
        tree = ast.parse(text)
    except Exception:
        continue

    found = []

    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            if any(
                keyword in node.name.lower()
                for keyword in keywords
            ):
                found.append(
                    (
                        node.lineno,
                        type(node).__name__,
                        node.name,
                    )
                )

    if not found:
        continue

    write()
    write(relative(path))

    for line, kind, name in sorted(found):
        write(
            f"  {line:5d}: {kind:<18} {name}"
        )


# ======================================================================================
# 5. RESULTADO
# ======================================================================================

section("5. O QUE PRECISAMOS DESCOBRIR")

write(
    "[A] Qual componente busca IDs de partidas recentes?"
)
write(
    "[B] Qual componente baixa o Match JSON completo?"
)
write(
    "[C] Onde esses JSONs são persistidos?"
)
write(
    "[D] Existe cache impedindo atualização?"
)
write(
    "[E] Quantas partidas recentes o fluxo busca?"
)
write(
    "[F] Qual é a data da partida local mais recente?"
)
write(
    "[G] O pipeline atual já está preparado para TFTSet18?"
)

REPORT.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print("=" * 90)
print("TFT INSIGHT — MATCH COLLECTION AUDIT")
print("=" * 90)
print()
print(f"JSONs locais: {len(json_files)}")

if dated_matches:
    print(
        "Partida local mais recente:",
        dated_matches[0][0].isoformat(),
        dated_matches[0][2],
    )

print()
print("Relatório:")
print(REPORT)
print()
print("Nenhum arquivo do produto foi alterado.")
print("=" * 90)