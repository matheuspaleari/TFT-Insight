from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET = ROOT / "scripts" / "run_challenger_item_benchmark.py"

REPORT = ROOT / "challenger_benchmark_config_audit.txt"


# =============================================================================
# TFT INSIGHT
# ROADMAP 26 — AUDITORIA DO BENCHMARK CHALLENGER
#
# SOMENTE LEITURA.
#
# Objetivos:
# - descobrir onde quantidade de players é definida;
# - confirmar o valor atual (esperado: 50);
# - descobrir quantidade de partidas por player;
# - identificar argumentos CLI;
# - identificar Riot endpoints utilizados;
# - identificar cache/index;
# - descobrir se execução antiga impede baixar Set 18;
# - identificar como fazer um rebuild limpo;
# - preparar alteração futura para 100 players.
# =============================================================================


lines: list[str] = []


def write(value: str = "") -> None:
    lines.append(value)


def section(title: str) -> None:
    write()
    write("=" * 120)
    write(title)
    write("=" * 120)


def subsection(title: str) -> None:
    write()
    write("-" * 120)
    write(title)
    write("-" * 120)


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def clean(value: str, limit: int = 360) -> str:
    value = value.rstrip()

    if len(value) > limit:
        return value[: limit - 3] + "..."

    return value


def safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse unavailable>"


if not TARGET.exists():
    raise SystemExit(
        f"Arquivo não encontrado: {TARGET}"
    )


source = read_text(TARGET)
source_lines = source.splitlines()

tree = ast.parse(source)


# =============================================================================
# 1. Informações básicas
# =============================================================================

section("1. ARQUIVO AUDITADO")

write(f"Arquivo: {TARGET}")
write(f"Linhas : {len(source_lines)}")
write("Modo   : SOMENTE LEITURA")


# =============================================================================
# 2. Constantes / assignments
# =============================================================================

section("2. CONSTANTES E CONFIGURAÇÕES NUMÉRICAS")

keywords = (
    "player",
    "players",
    "challenger",
    "match",
    "matches",
    "count",
    "limit",
    "page",
    "cache",
    "retry",
    "sleep",
    "request",
    "benchmark",
)

assignments = []

for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        value = safe_unparse(node.value)

        for target in node.targets:
            target_text = safe_unparse(target)

            searchable = (
                target_text + " " + value
            ).lower()

            if any(
                keyword in searchable
                for keyword in keywords
            ):
                assignments.append(
                    (
                        node.lineno,
                        target_text,
                        value,
                    )
                )

    elif isinstance(node, ast.AnnAssign):
        target_text = safe_unparse(node.target)

        value = (
            safe_unparse(node.value)
            if node.value is not None
            else "<sem valor>"
        )

        searchable = (
            target_text + " " + value
        ).lower()

        if any(
            keyword in searchable
            for keyword in keywords
        ):
            assignments.append(
                (
                    node.lineno,
                    target_text,
                    value,
                )
            )


for line_number, name, value in sorted(assignments):
    write(
        f"{line_number:5d}: "
        f"{name} = {clean(value)}"
    )


# =============================================================================
# 3. Ocorrências do número 50 / 100
# =============================================================================

section("3. OCORRÊNCIAS DE 50 / 100")

number_regex = re.compile(
    r"(?<!\d)(50|100)(?!\d)"
)

found_numbers = 0

for number, line in enumerate(
    source_lines,
    start=1,
):
    if number_regex.search(line):
        found_numbers += 1

        write(
            f"{number:5d}: {clean(line)}"
        )

if not found_numbers:
    write(
        "Nenhuma ocorrência literal de 50 ou 100 encontrada."
    )


# =============================================================================
# 4. Argumentos CLI
# =============================================================================

section("4. ARGUMENTOS DE LINHA DE COMANDO")

cli_regex = re.compile(
    r"(ArgumentParser|add_argument|parse_args|"
    r"players|matches|count|limit)",
    re.IGNORECASE,
)

cli_hits = []

for number, line in enumerate(
    source_lines,
    start=1,
):
    if cli_regex.search(line):
        cli_hits.append(
            (
                number,
                clean(line),
            )
        )

for number, line in cli_hits[:200]:
    write(
        f"{number:5d}: {line}"
    )

if not cli_hits:
    write(
        "Nenhum argparse/config CLI aparente encontrado."
    )


# =============================================================================
# 5. Funções principais
# =============================================================================

section("5. FUNÇÕES PRINCIPAIS DO BENCHMARK")

definitions = []

for node in ast.walk(tree):
    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        if any(
            word in node.name.lower()
            for word in (
                "player",
                "challenger",
                "match",
                "collect",
                "download",
                "process",
                "cache",
                "index",
                "benchmark",
                "main",
            )
        ):
            definitions.append(
                (
                    node.lineno,
                    getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                    node.name,
                )
            )


for start, end, name in sorted(definitions):
    write(
        f"{start:5d}-{end:<5d} {name}"
    )


# =============================================================================
# 6. Código completo das funções críticas
# =============================================================================

section("6. CORPO DAS FUNÇÕES CRÍTICAS")

wanted_functions = {
    "collect_match_ids",
    "load_or_download_match",
    "process_matches",
    "main",
}


for start, end, name in sorted(definitions):
    if name not in wanted_functions:
        continue

    subsection(name)

    for number in range(start, end + 1):
        if number <= len(source_lines):
            write(
                f"{number:5d}: "
                f"{clean(source_lines[number - 1])}"
            )


# =============================================================================
# 7. Cache/index
# =============================================================================

section("7. CACHE / INDEX / ESTADO PERSISTIDO")

cache_regex = re.compile(
    r"(CACHE|INDEX|processed_match_ids|failed_match_ids|"
    r"match_ids|observations|classifications|"
    r"exists\(|load_|save_|unlink|rmtree|mkdir)",
    re.IGNORECASE,
)

cache_hits = []

for number, line in enumerate(
    source_lines,
    start=1,
):
    if cache_regex.search(line):
        cache_hits.append(
            (
                number,
                clean(line),
            )
        )

for number, line in cache_hits[:300]:
    write(
        f"{number:5d}: {line}"
    )


# =============================================================================
# 8. Paths do benchmark
# =============================================================================

section("8. PATHS / ARQUIVOS GERADOS")

path_regex = re.compile(
    r"(Path\(|CACHE|INDEX|OBSERVATIONS|CSV|JSON|"
    r"benchmark|challenger|role_inference)",
    re.IGNORECASE,
)

for number, line in enumerate(
    source_lines,
    start=1,
):
    if path_regex.search(line):
        write(
            f"{number:5d}: {clean(line)}"
        )


# =============================================================================
# 9. Riot API
# =============================================================================

section("9. CHAMADAS À RIOT API")

riot_regex = re.compile(
    r"(get_challenger|get_match_ids|get_match_details|"
    r"league|challenger|puuid|summoner)",
    re.IGNORECASE,
)

for number, line in enumerate(
    source_lines,
    start=1,
):
    if riot_regex.search(line):
        write(
            f"{number:5d}: {clean(line)}"
        )


# =============================================================================
# 10. get_match_ids com contexto
# =============================================================================

section("10. CONTEXTO DE get_match_ids")

for number, line in enumerate(
    source_lines,
    start=1,
):
    if "get_match_ids" not in line:
        continue

    start = max(
        1,
        number - 12,
    )

    end = min(
        len(source_lines),
        number + 18,
    )

    subsection(
        f"get_match_ids próximo da linha {number}"
    )

    for current in range(start, end + 1):
        write(
            f"{current:5d}: "
            f"{clean(source_lines[current - 1])}"
        )


# =============================================================================
# 11. Loops de players
# =============================================================================

section("11. LOOPS / LIMITES DE PLAYERS")

player_regex = re.compile(
    r"(players|player|entries|challenger|"
    r"\[:|enumerate|range\(|limit)",
    re.IGNORECASE,
)

for number, line in enumerate(
    source_lines,
    start=1,
):
    if player_regex.search(line):
        write(
            f"{number:5d}: {clean(line)}"
        )


# =============================================================================
# 12. Possíveis bloqueios para rebuild
# =============================================================================

section("12. POSSÍVEIS BLOQUEIOS PARA REBUILD DO SET 18")

patterns = (
    "processed_match_ids",
    "failed_match_ids",
    "if path.exists",
    "if filepath.exists",
    "já existe",
    "skip",
    "continue",
)

for number, line in enumerate(
    source_lines,
    start=1,
):
    if any(
        pattern.lower() in line.lower()
        for pattern in patterns
    ):
        write(
            f"{number:5d}: {clean(line)}"
        )


# =============================================================================
# 13. Conclusões que precisamos responder
# =============================================================================

section("13. CHECKLIST PARA A ALTERAÇÃO")

questions = (
    "[A] Onde exatamente está definido o limite atual de 50 players?",
    "[B] O limite é constante, slicing ou argumento CLI?",
    "[C] Podemos alterar com segurança para 100?",
    "[D] Quantas partidas são buscadas por player?",
    "[E] Existe paginação de match IDs?",
    "[F] O script busca Challenger atual a cada execução?",
    "[G] O índice antigo reutiliza os jogadores antigos?",
    "[H] O índice antigo impede baixar partidas novas?",
    "[I] processed_match_ids precisa ser limpo?",
    "[J] failed_match_ids precisa ser limpo?",
    "[K] cache de JSON precisa ser apagado?",
    "[L] item_observations antigas precisam ser separadas por Set?",
    "[M] item_classifications antigas precisam ser regeneradas?",
    "[N] O benchmark possui filtro de Set?",
    "[O] Precisamos adicionar filtro TFTSet18?",
    "[P] Como garantir que Set 17 não contamine Set 18?",
    "[Q] Qual comando final deve executar 100 players?",
)

for question in questions:
    write(question)


# =============================================================================
# 14. Segurança
# =============================================================================

section("14. SEGURANÇA")

write(
    "Nenhum arquivo do projeto foi modificado."
)

write(
    "Nenhum cache foi apagado."
)

write(
    "Nenhuma chamada Riot foi executada."
)

write(
    "Nenhum benchmark foi iniciado."
)


REPORT.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)


print("=" * 90)
print("TFT INSIGHT — CHALLENGER BENCHMARK CONFIG AUDIT")
print("=" * 90)
print()
print("Auditoria concluída.")
print("Modo: SOMENTE LEITURA")
print()
print("Relatório:")
print(REPORT)
print()
print("Meta da próxima alteração: 100 players.")
print("=" * 90)