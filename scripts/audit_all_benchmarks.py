from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REPORT = ROOT / "all_benchmarks_audit.txt"


# =============================================================================
# TFT INSIGHT
# AUDITORIA GERAL DE BENCHMARKS
#
# SOMENTE LEITURA.
#
# Objetivos:
# - identificar todos os benchmarks suportados;
# - localizar limites de players;
# - localizar defaults como 50 / 100;
# - identificar quantidade de partidas por player;
# - descobrir como players são selecionados;
# - descobrir quais tiers/ranks são usados;
# - identificar cache/index/estado por benchmark;
# - descobrir se existe um runner central;
# - verificar se benchmarks compartilham o mesmo coletor;
# - identificar riscos de mistura entre Set 17 / Set 18;
# - preparar rebuild de TODOS os benchmarks com 100 players.
# =============================================================================


SEARCH_EXTENSIONS = {
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "scripts/archive",
}


BENCHMARK_TERMS = (
    "benchmark",
    "benchmarks",
    "challenger",
    "grandmaster",
    "master",
    "diamond",
    "emerald",
    "platinum",
    "gold",
    "silver",
    "bronze",
    "iron",
    "advanced",
    "competitive",
    "apex",
)


CONFIG_TERMS = (
    "players",
    "player_limit",
    "players_limit",
    "limit",
    "matches_per_player",
    "match_count",
    "matches",
    "batch_size",
    "tier",
    "queue",
)


STATE_TERMS = (
    "cache",
    "index",
    "state",
    "observations",
    "classifications",
    "processed_match_ids",
    "failed_match_ids",
    "match_ids",
    "summary",
    "report",
)


SET_TERMS = (
    "tft_set_core_name",
    "tft_set_number",
    "set_number",
    "set_name",
    "TFTSet17",
    "TFTSet18",
)


# =============================================================================
# Reporter
# =============================================================================


class Reporter:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def write(self, value: str = "") -> None:
        self.lines.append(value)

    def section(self, title: str) -> None:
        self.write()
        self.write("=" * 120)
        self.write(title)
        self.write("=" * 120)

    def subsection(self, title: str) -> None:
        self.write()
        self.write("-" * 120)
        self.write(title)
        self.write("-" * 120)

    def save(self, path: Path) -> None:
        path.write_text(
            "\n".join(self.lines) + "\n",
            encoding="utf-8",
        )


R = Reporter()


# =============================================================================
# Helpers
# =============================================================================


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except Exception:
        return str(path)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return None


def clean(value: str, limit: int = 360) -> str:
    value = value.rstrip().replace("\t", "    ")

    if len(value) > limit:
        return value[: limit - 3] + "..."

    return value


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        rel = relative(path)

        if any(
            ignored in rel
            for ignored in IGNORED_DIRS
        ):
            continue

        if path.suffix.lower() not in SEARCH_EXTENSIONS:
            continue

        yield path


def parse_python(path: Path) -> ast.Module | None:
    text = read_text(path)

    if text is None:
        return None

    try:
        return ast.parse(text)
    except Exception:
        return None


def safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse unavailable>"


# =============================================================================
# 1. Candidate benchmark files
# =============================================================================


def find_benchmark_files():
    candidates = []

    for path in iter_files():
        text = read_text(path)

        if text is None:
            continue

        lowered = (
            relative(path)
            + "\n"
            + text
        ).lower()

        score = sum(
            lowered.count(term.lower())
            for term in BENCHMARK_TERMS
        )

        if score <= 0:
            continue

        candidates.append(
            (
                score,
                path,
                text,
            )
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            relative(item[1]).lower(),
        )
    )

    return candidates


# =============================================================================
# 2. Benchmark names / tiers
# =============================================================================


def audit_benchmark_names(candidates) -> None:
    R.section("1. BENCHMARKS / TIERS IDENTIFICADOS")

    benchmark_name_regex = re.compile(
        r"(CHALLENGER|GRANDMASTER|MASTER|DIAMOND|EMERALD|"
        r"PLATINUM|GOLD|SILVER|BRONZE|IRON|ADVANCED|"
        r"COMPETITIVE)",
        re.IGNORECASE,
    )

    hits = defaultdict(list)

    for _, path, text in candidates:
        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            match = benchmark_name_regex.search(line)

            if not match:
                continue

            key = match.group(1).upper()

            hits[key].append(
                (
                    path,
                    number,
                    clean(line),
                )
            )

    if not hits:
        R.write(
            "Nenhum nome explícito de benchmark/tier encontrado."
        )
        return

    for name in sorted(hits):
        R.subsection(name)

        for path, number, line in hits[name][:80]:
            R.write(
                f"{relative(path)}:{number}: {line}"
            )


# =============================================================================
# 3. Files ranked
# =============================================================================


def audit_candidate_files(candidates) -> None:
    R.section("2. ARQUIVOS MAIS RELACIONADOS A BENCHMARK")

    for index, (score, path, _) in enumerate(
        candidates[:120],
        start=1,
    ):
        R.write(
            f"[{index:03d}] score={score:<4} {relative(path)}"
        )


# =============================================================================
# 4. Numeric configuration
# =============================================================================


def audit_numeric_config(candidates) -> None:
    R.section("3. LIMITES / PLAYERS / MATCHES / BATCH")

    number_regex = re.compile(
        r"(?<!\d)(20|25|30|40|50|75|100|150|200)(?!\d)"
    )

    config_regex = re.compile(
        r"(players?|matches?|batch|limit|count|benchmark|tier)",
        re.IGNORECASE,
    )

    found = 0

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if (
                config_regex.search(line)
                and number_regex.search(line)
            ):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        found += 1
        R.subsection(relative(path))

        for number, line in hits[:100]:
            R.write(
                f"{number:5d}: {line}"
            )

    if not found:
        R.write(
            "Nenhuma configuração numérica relevante encontrada."
        )


# =============================================================================
# 5. Assignments
# =============================================================================


def audit_assignments(candidates) -> None:
    R.section("4. CONSTANTES / CONFIGURAÇÕES VIA AST")

    for _, path, _ in candidates:
        if path.suffix.lower() != ".py":
            continue

        tree = parse_python(path)

        if tree is None:
            continue

        assignments = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    name = safe_unparse(target)
                    value = safe_unparse(node.value)

                    searchable = (
                        name + " " + value
                    ).lower()

                    if any(
                        term in searchable
                        for term in CONFIG_TERMS
                    ):
                        assignments.append(
                            (
                                node.lineno,
                                name,
                                value,
                            )
                        )

            elif isinstance(node, ast.AnnAssign):
                name = safe_unparse(node.target)

                value = (
                    safe_unparse(node.value)
                    if node.value is not None
                    else "<sem valor>"
                )

                searchable = (
                    name + " " + value
                ).lower()

                if any(
                    term in searchable
                    for term in CONFIG_TERMS
                ):
                    assignments.append(
                        (
                            node.lineno,
                            name,
                            value,
                        )
                    )

        if not assignments:
            continue

        R.subsection(relative(path))

        for number, name, value in assignments[:120]:
            R.write(
                f"{number:5d}: "
                f"{name} = {clean(value)}"
            )


# =============================================================================
# 6. CLI arguments
# =============================================================================


def audit_cli(candidates) -> None:
    R.section("5. ARGUMENTOS CLI DOS RUNNERS")

    cli_regex = re.compile(
        r"(ArgumentParser|add_argument|parse_args|"
        r"--players|--matches|--benchmark|--tier|"
        r"--reset|--refresh|--batch)",
        re.IGNORECASE,
    )

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if cli_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:160]:
            R.write(
                f"{number:5d}: {line}"
            )


# =============================================================================
# 7. Player selection
# =============================================================================


def audit_player_selection(candidates) -> None:
    R.section("6. COMO JOGADORES SÃO SELECIONADOS")

    selection_regex = re.compile(
        r"(get_apex_league_players|get_league|"
        r"CHALLENGER|GRANDMASTER|MASTER|DIAMOND|"
        r"EMERALD|PLATINUM|GOLD|SILVER|BRONZE|IRON|"
        r"tier\s*=|queue\s*=|limit\s*=)",
        re.IGNORECASE,
    )

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if selection_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:180]:
            R.write(
                f"{number:5d}: {line}"
            )


# =============================================================================
# 8. Match collection
# =============================================================================


def audit_match_collection(candidates) -> None:
    R.section("7. COLETA DE MATCH IDS / DETALHES")

    match_regex = re.compile(
        r"(get_match_ids|get_match_details|"
        r"matches_per_player|match_count|"
        r"count\s*=|start\s*=|page)",
        re.IGNORECASE,
    )

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if match_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:180]:
            R.write(
                f"{number:5d}: {line}"
            )


# =============================================================================
# 9. State/cache paths
# =============================================================================


def audit_state_paths(candidates) -> None:
    R.section("8. CACHE / INDEX / ESTADO POR BENCHMARK")

    state_regex = re.compile(
        r"(STATE_DIRECTORY|CACHE|INDEX|OBSERVATIONS|"
        r"CLASSIFICATIONS|SUMMARY|REPORT|"
        r"processed_match_ids|failed_match_ids|"
        r"Path\(|mkdir|unlink|rmtree)",
        re.IGNORECASE,
    )

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if state_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:200]:
            R.write(
                f"{number:5d}: {line}"
            )


# =============================================================================
# 10. Shared collector/service
# =============================================================================


def audit_shared_services(candidates) -> None:
    R.section("9. SERVIÇOS / COLETORES COMPARTILHADOS")

    service_regex = re.compile(
        r"(BenchmarkCollector|CachedMatchService|"
        r"RiotClient|collect_players_metrics|"
        r"collect_match_ids|benchmark_collector|"
        r"get_apex_league_players)",
        re.IGNORECASE,
    )

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if service_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:180]:
            R.write(
                f"{number:5d}: {line}"
            )


# =============================================================================
# 11. Benchmark names in API/UI
# =============================================================================


def audit_api_ui(candidates) -> None:
    R.section("10. BENCHMARKS EXPOSTOS NA API / UI")

    api_ui_regex = re.compile(
        r"(benchmark|advanced|competitive|challenger|"
        r"grandmaster|master|diamond|emerald|platinum|"
        r"selectbox|radio|option|enum)",
        re.IGNORECASE,
    )

    for _, path, text in candidates:
        rel = relative(path).lower()

        if not (
            "api" in rel
            or "route" in rel
            or "streamlit" in rel
            or "partner_platform" in rel
            or "page" in rel
            or "contract" in rel
        ):
            continue

        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if api_ui_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:160]:
            R.write(
                f"{number:5d}: {line}"
            )


# =============================================================================
# 12. Set filtering
# =============================================================================


def audit_set_filtering(candidates) -> None:
    R.section("11. FILTRO DE SET / RISCO DE CONTAMINAÇÃO")

    set_regex = re.compile(
        r"(tft_set_core_name|tft_set_number|"
        r"set_number|set_name|TFTSet17|TFTSet18|"
        r"current_set|target_set)",
        re.IGNORECASE,
    )

    total_hits = 0

    for _, path, text in candidates:
        hits = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if set_regex.search(line):
                hits.append(
                    (
                        number,
                        clean(line),
                    )
                )

        if not hits:
            continue

        total_hits += len(hits)

        R.subsection(relative(path))

        for number, line in hits[:180]:
            R.write(
                f"{number:5d}: {line}"
            )

    if total_hits == 0:
        R.write(
            "Nenhum filtro explícito de Set encontrado nos arquivos "
            "relacionados a benchmark."
        )


# =============================================================================
# 13. Functions/classes
# =============================================================================


def audit_definitions(candidates) -> None:
    R.section("12. FUNÇÕES / CLASSES IMPORTANTES")

    keywords = (
        "benchmark",
        "collect",
        "player",
        "match",
        "league",
        "tier",
        "cache",
        "index",
        "report",
        "main",
    )

    for _, path, _ in candidates:
        if path.suffix.lower() != ".py":
            continue

        tree = parse_python(path)

        if tree is None:
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

        R.subsection(relative(path))

        for line, kind, name in sorted(found):
            R.write(
                f"{line:5d}: {kind:<18} {name}"
            )


# =============================================================================
# 14. Likely runners
# =============================================================================


def audit_runners(candidates) -> None:
    R.section("13. RUNNERS PROVÁVEIS DE BENCHMARK")

    for score, path, text in candidates:
        rel = relative(path).lower()

        runner_like = (
            path.suffix.lower() == ".py"
            and (
                path.name.startswith("run_")
                or "benchmark" in path.name.lower()
                or 'if __name__ == "__main__"' in text
            )
        )

        if not runner_like:
            continue

        R.write(
            f"score={score:<4} {relative(path)}"
        )


# =============================================================================
# 15. Checklist
# =============================================================================


def audit_checklist() -> None:
    R.section("14. CHECKLIST PARA REBUILD COM 100 PLAYERS")

    questions = [
        "[A] Quais benchmarks existem oficialmente no produto?",
        "[B] Quais deles são ranks reais da Riot?",
        "[C] Quais são agrupamentos internos como advanced/competitive?",
        "[D] Existe um runner por benchmark ou um runner genérico?",
        "[E] O limite de 50 está centralizado ou duplicado?",
        "[F] Podemos passar 100 por argumento sem alterar código?",
        "[G] Devemos mudar o default global para 100?",
        "[H] Quantas partidas por player cada benchmark usa?",
        "[I] Todos usam 30 partidas?",
        "[J] Todos compartilham o mesmo RiotClient?",
        "[K] Todos compartilham o mesmo cache?",
        "[L] O estado é separado por benchmark?",
        "[M] O estado é separado por Set?",
        "[N] Existe filtro explícito de TFTSet18?",
        "[O] Como impedir Set 17 de contaminar Set 18?",
        "[P] Precisamos manter benchmark por tier separado?",
        "[Q] Precisamos criar diretório por Set e benchmark?",
        "[R] Como rodar TODOS os benchmarks com 100 players?",
        "[S] Quanto pode aumentar o volume total de partidas?",
        "[T] Quais etapas podem ser retomadas após interrupção?",
    ]

    for question in questions:
        R.write(question)


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    candidates = find_benchmark_files()

    R.section("TFT INSIGHT — AUDITORIA GERAL DE BENCHMARKS")

    R.write(
        f"Arquivos candidatos encontrados: {len(candidates)}"
    )

    R.write(
        "Modo: SOMENTE LEITURA"
    )

    audit_benchmark_names(candidates)
    audit_candidate_files(candidates)
    audit_numeric_config(candidates)
    audit_assignments(candidates)
    audit_cli(candidates)
    audit_player_selection(candidates)
    audit_match_collection(candidates)
    audit_state_paths(candidates)
    audit_shared_services(candidates)
    audit_api_ui(candidates)
    audit_set_filtering(candidates)
    audit_definitions(candidates)
    audit_runners(candidates)
    audit_checklist()

    R.section("15. SEGURANÇA")

    R.write(
        "Nenhum arquivo do produto foi modificado."
    )

    R.write(
        "Nenhum benchmark foi executado."
    )

    R.write(
        "Nenhuma chamada à Riot API foi realizada."
    )

    R.write(
        "Nenhum cache foi apagado."
    )

    R.save(REPORT)

    print("=" * 90)
    print("TFT INSIGHT — ALL BENCHMARKS AUDIT")
    print("=" * 90)
    print()
    print(
        f"Arquivos candidatos: {len(candidates)}"
    )
    print()
    print("Relatório:")
    print(REPORT)
    print()
    print("Nenhum benchmark foi executado.")
    print("=" * 90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())