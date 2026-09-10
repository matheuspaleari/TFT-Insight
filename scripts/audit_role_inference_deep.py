from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ======================================================================================
# TFT INSIGHT
# AUDITORIA PROFUNDA — ROLE INFERENCE / CARRY DETECTOR FOUNDATION
#
# Objetivo:
#
#   Entender exatamente:
#
#   Riot Match / UnitSnapshot
#       ↓
#   StatisticalItemClassifier
#       ↓
#   RoleInferenceEngine.infer_unit()
#       ↓
#   scores por função
#       ↓
#   _select_main_role()
#       ↓
#   ParticipantRoleReport
#       ↓
#   damage_carry / main_tank / support
#
# Essa auditoria é SOMENTE LEITURA.
#
# Não:
#   - altera arquivos;
#   - importa módulos do TFT Insight;
#   - chama Riot API;
#   - inicia FastAPI;
#   - inicia Streamlit;
#   - grava nada além do próprio relatório TXT.
#
# O TXT é uma saída da ferramenta de auditoria, não uma alteração de código do produto.
# ======================================================================================


AUDIT_VERSION = "1.0"

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILE = ROOT / "role_inference_deep_audit.txt"


PRIMARY_FILES = [
    ROOT / "src/role_inference/services/role_inference_engine.py",
    ROOT / "src/role_inference/services/statistical_item_classifier.py",
    ROOT / "src/role_inference/models/unit_role.py",
]


POSSIBLE_RELATED_FILES = [
    ROOT / "src/role_inference/models/participant_role_report.py",
    ROOT / "src/role_inference/models/unit_role_assessment.py",
    ROOT / "src/role_inference/models/__init__.py",
    ROOT / "src/role_inference/services/__init__.py",
    ROOT / "src/role_inference/__init__.py",
]


SEARCH_EXTENSIONS = {
    ".py",
    ".json",
    ".yaml",
    ".yml",
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
    "archive",
}


ROLE_WORDS = {
    "carry",
    "damage_carry",
    "main_tank",
    "tank",
    "support",
    "utility",
    "role",
    "roles",
    "role_report",
    "role_inference",
    "unit_role",
    "assessment",
}


SIGNAL_WORDS = {
    "item",
    "items",
    "tier",
    "rarity",
    "star",
    "stars",
    "character_id",
    "score",
    "scores",
    "weight",
    "weights",
    "bonus",
    "penalty",
    "confidence",
    "threshold",
    "damage",
    "tank",
    "support",
    "carry",
}


STATIC_WORDS = {
    "communitydragon",
    "datadragon",
    "static_data",
    "item_classifier",
    "metadata",
    "item_data",
    "unit_data",
    "champion_data",
}


# ======================================================================================
# Output
# ======================================================================================


class Reporter:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def write(self, text: str = "") -> None:
        self.lines.append(text)

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


# ======================================================================================
# Helpers
# ======================================================================================


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def clean(text: str, max_len: int = 260) -> str:
    text = text.replace("\t", "    ").rstrip()

    if len(text) > max_len:
        return text[: max_len - 3] + "..."

    return text


def iter_python_files() -> Iterable[Path]:
    for path in ROOT.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def source_lines(path: Path) -> list[str]:
    text = read_text(path)

    if text is None:
        return []

    return text.splitlines()


def print_lines(
    path: Path,
    start: int,
    end: int,
    *,
    title: str | None = None,
) -> None:
    lines = source_lines(path)

    if not lines:
        return

    start = max(start, 1)
    end = min(end, len(lines))

    if title:
        R.subsection(title)

    for number in range(start, end + 1):
        R.write(f"{number:5d}: {clean(lines[number - 1])}")


# ======================================================================================
# AST Models
# ======================================================================================


@dataclass
class Definition:
    name: str
    kind: str
    line: int
    end_line: int


@dataclass
class Assignment:
    name: str
    line: int
    value: str


@dataclass
class ImportRef:
    line: int
    module: str


def safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse unavailable>"


def parse_python(path: Path) -> ast.Module | None:
    text = read_text(path)

    if text is None:
        return None

    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def collect_definitions(tree: ast.Module) -> list[Definition]:
    output: list[Definition] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            output.append(
                Definition(
                    name=node.name,
                    kind="class",
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )

        elif isinstance(node, ast.FunctionDef):
            output.append(
                Definition(
                    name=node.name,
                    kind="function",
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )

        elif isinstance(node, ast.AsyncFunctionDef):
            output.append(
                Definition(
                    name=node.name,
                    kind="async function",
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )

    return sorted(
        output,
        key=lambda item: item.line,
    )


def assignment_target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        return safe_unparse(node)

    return None


def collect_assignments(tree: ast.Module) -> list[Assignment]:
    output: list[Assignment] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = assignment_target_name(target)

                if not name:
                    continue

                output.append(
                    Assignment(
                        name=name,
                        line=node.lineno,
                        value=clean(
                            safe_unparse(node.value),
                            max_len=300,
                        ),
                    )
                )

        elif isinstance(node, ast.AnnAssign):
            name = assignment_target_name(node.target)

            if not name:
                continue

            output.append(
                Assignment(
                    name=name,
                    line=node.lineno,
                    value=clean(
                        safe_unparse(node.value)
                        if node.value is not None
                        else "<annotation only>",
                        max_len=300,
                    ),
                )
            )

    return sorted(
        output,
        key=lambda item: item.line,
    )


def collect_imports(tree: ast.Module) -> list[ImportRef]:
    output: list[ImportRef] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                output.append(
                    ImportRef(
                        line=node.lineno,
                        module=alias.name,
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""

            for alias in node.names:
                module = (
                    f"{base}.{alias.name}"
                    if base
                    else alias.name
                )

                output.append(
                    ImportRef(
                        line=node.lineno,
                        module=module,
                    )
                )

    return sorted(
        output,
        key=lambda item: item.line,
    )


# ======================================================================================
# 1. Files
# ======================================================================================


def audit_files() -> list[Path]:
    R.section("1. ARQUIVOS DA CAMADA ROLE INFERENCE")

    existing: list[Path] = []

    for path in PRIMARY_FILES + POSSIBLE_RELATED_FILES:
        status = "OK" if path.exists() else "NÃO ENCONTRADO"

        R.write(
            f"{status:<15} {relative(path)}"
        )

        if path.exists():
            existing.append(path)

    role_dir = ROOT / "src/role_inference"

    if role_dir.exists():
        R.write()
        R.write("Conteúdo completo de src/role_inference:")

        for path in sorted(role_dir.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                R.write(f"  {relative(path)}")

    return existing


# ======================================================================================
# 2. Definitions
# ======================================================================================


def audit_definitions(files: list[Path]) -> None:
    R.section("2. CLASSES E FUNÇÕES")

    for path in files:
        if path.suffix != ".py":
            continue

        tree = parse_python(path)

        if tree is None:
            continue

        R.subsection(relative(path))

        definitions = collect_definitions(tree)

        if not definitions:
            R.write("Nenhuma definição encontrada.")
            continue

        for item in definitions:
            R.write(
                f"{item.line:5d}-{item.end_line:<5d} "
                f"{item.kind:<16} {item.name}"
            )


# ======================================================================================
# 3. Full role engine
# ======================================================================================


def audit_role_engine_source() -> None:
    path = ROOT / "src/role_inference/services/role_inference_engine.py"

    R.section("3. ROLE INFERENCE ENGINE — CÓDIGO COMPLETO")

    if not path.exists():
        R.write("Arquivo não encontrado.")
        return

    lines = source_lines(path)

    for number, line in enumerate(lines, start=1):
        R.write(
            f"{number:5d}: {clean(line, max_len=360)}"
        )


# ======================================================================================
# 4. Statistical classifier
# ======================================================================================


def audit_classifier_source() -> None:
    path = ROOT / "src/role_inference/services/statistical_item_classifier.py"

    R.section("4. STATISTICAL ITEM CLASSIFIER — CÓDIGO COMPLETO")

    if not path.exists():
        R.write("Arquivo não encontrado.")
        return

    lines = source_lines(path)

    for number, line in enumerate(lines, start=1):
        R.write(
            f"{number:5d}: {clean(line, max_len=360)}"
        )


# ======================================================================================
# 5. Role models
# ======================================================================================


def audit_role_models() -> None:
    R.section("5. MODELOS / CONTRATOS DE ROLE")

    role_dir = ROOT / "src/role_inference/models"

    if not role_dir.exists():
        R.write("Diretório src/role_inference/models não encontrado.")
        return

    files = sorted(role_dir.glob("*.py"))

    for path in files:
        R.subsection(relative(path))

        lines = source_lines(path)

        for number, line in enumerate(lines, start=1):
            R.write(
                f"{number:5d}: {clean(line, max_len=340)}"
            )


# ======================================================================================
# 6. Weights / constants / thresholds
# ======================================================================================


def looks_like_scoring_assignment(item: Assignment) -> bool:
    name = item.name.lower()
    value = item.value.lower()

    indicators = (
        "score",
        "weight",
        "bonus",
        "penalty",
        "threshold",
        "confidence",
        "carry",
        "tank",
        "support",
        "damage",
        "rarity",
        "tier",
        "star",
        "item",
    )

    return any(
        indicator in name or indicator in value
        for indicator in indicators
    )


def audit_scoring_formula(files: list[Path]) -> None:
    R.section("6. PESOS / BÔNUS / PENALIDADES / THRESHOLDS")

    found = 0

    for path in files:
        if path.suffix != ".py":
            continue

        tree = parse_python(path)

        if tree is None:
            continue

        assignments = [
            item
            for item in collect_assignments(tree)
            if looks_like_scoring_assignment(item)
        ]

        if not assignments:
            continue

        found += 1
        R.subsection(relative(path))

        for item in assignments:
            R.write(
                f"{item.line:5d}: "
                f"{item.name} = {item.value}"
            )

    if not found:
        R.write(
            "Nenhum peso/threshold explícito identificado por AST."
        )


# ======================================================================================
# 7. Item role classification
# ======================================================================================


def audit_item_role_signals() -> None:
    R.section("7. COMO ITENS CONTRIBUEM PARA CARRY / TANK / SUPPORT")

    target_files = [
        ROOT / "src/role_inference/services/role_inference_engine.py",
        ROOT / "src/role_inference/services/statistical_item_classifier.py",
    ]

    regex = re.compile(
        r"(item|carry|damage|tank|support|utility|score|classif|role)",
        re.IGNORECASE,
    )

    for path in target_files:
        if not path.exists():
            continue

        R.subsection(relative(path))

        for number, line in enumerate(
            source_lines(path),
            start=1,
        ):
            if regex.search(line):
                R.write(
                    f"{number:5d}: {clean(line, max_len=360)}"
                )


# ======================================================================================
# 8. UnitSnapshot
# ======================================================================================


def audit_unit_snapshot() -> None:
    R.section("8. UNIT SNAPSHOT / PARTICIPANT SNAPSHOT")

    candidates: list[tuple[Path, int, str]] = []

    regex = re.compile(
        r"\b(class\s+UnitSnapshot|class\s+ParticipantSnapshot|"
        r"UnitSnapshot\s*=|ParticipantSnapshot\s*=)",
        re.IGNORECASE,
    )

    for path in iter_python_files():
        text = read_text(path)

        if text is None:
            continue

        if not regex.search(text):
            continue

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if regex.search(line):
                candidates.append(
                    (path, number, line)
                )

    if not candidates:
        R.write("UnitSnapshot/ParticipantSnapshot não encontrados.")
        return

    seen: set[Path] = set()

    for path, line_number, _ in candidates:
        if path in seen:
            continue

        seen.add(path)

        tree = parse_python(path)

        if tree is None:
            continue

        definitions = collect_definitions(tree)

        target_defs = [
            item
            for item in definitions
            if item.name
            in {
                "UnitSnapshot",
                "ParticipantSnapshot",
            }
        ]

        for definition in target_defs:
            R.subsection(
                f"{relative(path)} :: {definition.name}"
            )

            print_lines(
                path,
                definition.line,
                definition.end_line,
            )


# ======================================================================================
# 9. Role report consumers
# ======================================================================================


def audit_consumers() -> None:
    R.section("9. QUEM CONSOME damage_carry / main_tank / support")

    patterns = [
        re.compile(r"damage_carry", re.IGNORECASE),
        re.compile(r"main_tank", re.IGNORECASE),
        re.compile(r"role_report", re.IGNORECASE),
    ]

    matches: dict[Path, list[tuple[int, str]]] = defaultdict(list)

    for path in iter_python_files():
        if "audit_role_inference_deep.py" in path.name:
            continue

        lines = source_lines(path)

        for number, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in patterns):
                matches[path].append(
                    (number, clean(line, max_len=340))
                )

    if not matches:
        R.write("Nenhum consumidor encontrado.")
        return

    for path in sorted(
        matches,
        key=lambda p: relative(p).lower(),
    ):
        R.subsection(relative(path))

        for number, line in matches[path]:
            R.write(f"{number:5d}: {line}")


# ======================================================================================
# 10. Parallel carry selectors
# ======================================================================================


def audit_parallel_carry_selectors() -> None:
    R.section("10. SELETORES PARALELOS DE CARRY")

    patterns = [
        re.compile(r"def\s+.*select.*carry", re.IGNORECASE),
        re.compile(r"def\s+.*carry", re.IGNORECASE),
        re.compile(r"_validated_carry", re.IGNORECASE),
        re.compile(r"_legacy_select_carry", re.IGNORECASE),
        re.compile(r"_select_carry", re.IGNORECASE),
    ]

    results: dict[Path, list[tuple[int, str]]] = defaultdict(list)

    for path in iter_python_files():
        if path.name.startswith("audit_"):
            continue

        lines = source_lines(path)

        for number, line in enumerate(lines, start=1):
            if any(pattern.search(line) for pattern in patterns):
                results[path].append(
                    (number, clean(line))
                )

    if not results:
        R.write("Nenhum seletor paralelo encontrado.")
        return

    for path in sorted(
        results,
        key=lambda p: relative(p).lower(),
    ):
        R.subsection(relative(path))

        for number, line in results[path]:
            R.write(
                f"{number:5d}: {line}"
            )


# ======================================================================================
# 11. Exact function bodies of suspicious selectors
# ======================================================================================


SELECTOR_NAMES = {
    "infer_unit",
    "_select_main_role",
    "_legacy_select_carry",
    "_select_carry",
    "_validated_carry",
}


def audit_selector_bodies() -> None:
    R.section("11. CORPO COMPLETO DOS PRINCIPAIS SELETORES")

    for path in iter_python_files():
        tree = parse_python(path)

        if tree is None:
            continue

        definitions = collect_definitions(tree)

        selected = [
            item
            for item in definitions
            if item.name in SELECTOR_NAMES
        ]

        for definition in selected:
            R.subsection(
                f"{relative(path)} :: {definition.name}"
            )

            print_lines(
                path,
                definition.line,
                definition.end_line,
            )


# ======================================================================================
# 12. Confidence
# ======================================================================================


def audit_confidence() -> None:
    R.section("12. CONFIDENCE / THRESHOLD / NÃO CLASSIFICADO")

    regex = re.compile(
        r"(confidence|threshold|unknown|unclassified|"
        r"not_evaluated|none|ambiguous|insufficient)",
        re.IGNORECASE,
    )

    targets = [
        ROOT / "src/role_inference",
        ROOT / "src/carry_item_intelligence",
        ROOT / "src/decision_engine/analyzers/composition_identity_analyzer.py",
        ROOT / "src/decision_engine/analyzers/contest_analyzer.py",
    ]

    results: dict[Path, list[tuple[int, str]]] = defaultdict(list)

    for target in targets:
        if not target.exists():
            continue

        paths: Iterable[Path]

        if target.is_file():
            paths = [target]
        else:
            paths = target.rglob("*.py")

        for path in paths:
            lines = source_lines(path)

            for number, line in enumerate(lines, start=1):
                if regex.search(line):
                    results[path].append(
                        (
                            number,
                            clean(line, max_len=340),
                        )
                    )

    if not results:
        R.write(
            "Nenhum mecanismo claro de confidence/threshold encontrado."
        )
        return

    for path in sorted(
        results,
        key=lambda p: relative(p).lower(),
    ):
        R.subsection(relative(path))

        for number, line in results[path]:
            R.write(f"{number:5d}: {line}")


# ======================================================================================
# 13. Static data references
# ======================================================================================


def audit_static_data_usage() -> None:
    R.section("13. STATIC DATA USADO PELA ROLE INFERENCE")

    regex = re.compile(
        r"(communitydragon|datadragon|static_data|"
        r"item.*json|unit.*json|champion.*json|metadata)",
        re.IGNORECASE,
    )

    results: dict[Path, list[tuple[int, str]]] = defaultdict(list)

    for path in iter_python_files():
        text = read_text(path)

        if text is None:
            continue

        if "role_inference" not in text.lower():
            if "statistical_item_classifier" not in text.lower():
                continue

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if regex.search(line):
                results[path].append(
                    (number, clean(line))
                )

    if not results:
        R.write(
            "Nenhuma ligação direta entre role_inference e static data "
            "foi identificada por busca textual."
        )
        return

    for path in sorted(
        results,
        key=lambda p: relative(p).lower(),
    ):
        R.subsection(relative(path))

        for number, line in results[path]:
            R.write(f"{number:5d}: {line}")


# ======================================================================================
# 14. Existing static files
# ======================================================================================


def audit_static_files() -> None:
    R.section("14. STATIC DATA DISPONÍVEL NO PROJETO")

    static_root = ROOT / "data/static_data"

    if not static_root.exists():
        R.write("data/static_data não existe.")
        return

    regex = re.compile(
        r"(tft.*item|tft.*champ|tft.*unit|"
        r"tft.*trait|communitydragon|pt_br|pt_BR)",
        re.IGNORECASE,
    )

    count = 0

    for path in sorted(static_root.rglob("*")):
        if not path.is_file():
            continue

        rel = relative(path)

        if not regex.search(rel):
            continue

        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        R.write(
            f"{rel:<100} {size:>12,} bytes"
        )

        count += 1

        if count >= 150:
            R.write("... limite de 150 arquivos atingido.")
            break


# ======================================================================================
# 15. Scan fields in static TFT JSON
# ======================================================================================


def audit_static_schema() -> None:
    R.section("15. CAMPOS EXISTENTES NOS JSONS ESTÁTICOS")

    candidates = [
        ROOT / "data/static_data/communitydragon/latest/pt_br.json",
    ]

    # Adiciona arquivos conhecidos de Data Dragon.
    static_root = ROOT / "data/static_data"

    if static_root.exists():
        for path in static_root.rglob("*.json"):
            name = path.name.lower()

            if (
                "champ" in name
                or "unit" in name
                or "item" in name
                or "trait" in name
            ):
                candidates.append(path)

    seen: set[Path] = set()

    for path in candidates:
        if path in seen or not path.exists():
            continue

        seen.add(path)

        text = read_text(path)

        if text is None:
            continue

        R.subsection(relative(path))

        # Não parseamos tudo recursivamente para evitar relatórios gigantes.
        # Apenas levantamos nomes de campos JSON.
        field_regex = re.compile(
            r'"([^"]+)"\s*:'
        )

        fields: dict[str, int] = defaultdict(int)

        for match in field_regex.finditer(text):
            fields[match.group(1)] += 1

        interesting = []

        for field_name, frequency in fields.items():
            lower = field_name.lower()

            if any(
                signal in lower
                for signal in (
                    "name",
                    "api",
                    "cost",
                    "role",
                    "trait",
                    "item",
                    "stat",
                    "range",
                    "health",
                    "mana",
                    "damage",
                    "armor",
                    "magic",
                    "attack",
                    "speed",
                    "ability",
                    "icon",
                    "rarity",
                    "tier",
                )
            ):
                interesting.append(
                    (field_name, frequency)
                )

        interesting.sort(
            key=lambda item: (
                -item[1],
                item[0].lower(),
            )
        )

        for field_name, frequency in interesting[:120]:
            R.write(
                f"{field_name:<45} occurrences={frequency}"
            )


# ======================================================================================
# 16. Character-specific hardcoding
# ======================================================================================


def audit_character_hardcoding() -> None:
    R.section("16. POSSÍVEL HARDCODE DE CHAMPIONS / UNIDADES")

    # Procura comparações ou coleções de nomes dentro da camada role inference.
    role_root = ROOT / "src/role_inference"

    if not role_root.exists():
        R.write("src/role_inference não existe.")
        return

    champion_like = re.compile(
        r'["\'][A-Za-z][A-Za-z0-9_\- ]{2,30}["\']'
    )

    interesting_context = re.compile(
        r"(character|champion|unit|carry|tank|support|role)",
        re.IGNORECASE,
    )

    found = 0

    for path in role_root.rglob("*.py"):
        lines = source_lines(path)
        file_hits: list[tuple[int, str]] = []

        for number, line in enumerate(lines, start=1):
            if (
                champion_like.search(line)
                and interesting_context.search(line)
            ):
                file_hits.append(
                    (number, clean(line))
                )

        if file_hits:
            found += 1
            R.subsection(relative(path))

            for number, line in file_hits:
                R.write(
                    f"{number:5d}: {line}"
                )

    if not found:
        R.write(
            "Nenhum hardcode óbvio de champion encontrado."
        )


# ======================================================================================
# 17. Role propagation
# ======================================================================================


def audit_role_propagation() -> None:
    R.section("17. PROPAGAÇÃO DO RESULTADO DE ROLE PELO SISTEMA")

    regex = re.compile(
        r"(RoleInferenceEngine|ParticipantRoleReport|"
        r"damage_carry|main_tank|\.support\b)",
        re.IGNORECASE,
    )

    results: dict[Path, list[tuple[int, str]]] = defaultdict(list)

    for path in iter_python_files():
        if path.name == Path(__file__).name:
            continue

        lines = source_lines(path)

        for number, line in enumerate(lines, start=1):
            if regex.search(line):
                results[path].append(
                    (
                        number,
                        clean(line, max_len=350),
                    )
                )

    for path in sorted(
        results,
        key=lambda p: relative(p).lower(),
    ):
        R.subsection(relative(path))

        for number, line in results[path]:
            R.write(
                f"{number:5d}: {line}"
            )


# ======================================================================================
# 18. Architecture questions
# ======================================================================================


def audit_questions() -> None:
    R.section("18. CHECKLIST PARA O DESENHO DO CARRY DETECTOR V2")

    questions = [
        "[A] Quais scores existem hoje por unidade?",
        "[B] Quais itens aumentam damage/carry score?",
        "[C] Quais itens aumentam tank score?",
        "[D] Quais itens aumentam support/utility score?",
        "[E] O classifier usa dados estatísticos ou mappings manuais?",
        "[F] Tier/estrelas afetam qual score?",
        "[G] Rarity/custo afeta qual score?",
        "[H] Existe penalidade explícita para tank ser carry?",
        "[I] Existe penalidade explícita para support ser carry?",
        "[J] Existem stats do champion no cálculo?",
        "[K] Existe attack range/melee/backline no cálculo?",
        "[L] Existe trait no cálculo?",
        "[M] Existe dano individual da unidade no cálculo?",
        "[N] Existe confidence por unidade?",
        "[O] Existe threshold para aceitar damage_carry?",
        "[P] O sistema permite damage_carry=None?",
        "[Q] Como damage_carry é escolhido entre avaliações?",
        "[R] Como main_tank é escolhido?",
        "[S] Como support é escolhido?",
        "[T] Uma mesma unidade pode ocupar mais de um papel?",
        "[U] Existem fallbacks que ignoram RoleInferenceEngine?",
        "[V] Quantos módulos atualmente escolhem carry independentemente?",
        "[W] Existe static data útil ainda não aproveitado?",
        "[X] Existe qualquer hardcode por campeão?",
        "[Y] O atual UnitRole é suficiente para PRIMARY/SECONDARY carry?",
        "[Z] O resultado possui informação suficiente para confidence?",
    ]

    for question in questions:
        R.write(f"  {question}")


# ======================================================================================
# 19. Summary
# ======================================================================================


def audit_summary() -> None:
    R.section("19. RESUMO DA AUDITORIA")

    R.write(
        "Esta auditoria não decide ainda qual será o Carry Detector V2."
    )

    R.write()
    R.write(
        "O objetivo é produzir evidência suficiente para comparar:"
    )

    R.write()
    R.write(
        "  1. RoleInferenceEngine atual"
    )
    R.write(
        "  2. fallbacks paralelos existentes"
    )
    R.write(
        "  3. dados Riot realmente disponíveis"
    )
    R.write(
        "  4. static data disponível"
    )
    R.write(
        "  5. possibilidade de confidence/threshold"
    )

    R.write()
    R.write(
        "Nenhum arquivo do produto foi modificado."
    )


# ======================================================================================
# Main
# ======================================================================================


def main() -> int:
    if not ROOT.exists():
        print(
            f"Projeto não encontrado: {ROOT}",
            file=sys.stderr,
        )
        return 1

    files = audit_files()

    audit_definitions(files)
    audit_role_engine_source()
    audit_classifier_source()
    audit_role_models()
    audit_scoring_formula(files)
    audit_item_role_signals()
    audit_unit_snapshot()
    audit_consumers()
    audit_parallel_carry_selectors()
    audit_selector_bodies()
    audit_confidence()
    audit_static_data_usage()
    audit_static_files()
    audit_static_schema()
    audit_character_hardcoding()
    audit_role_propagation()
    audit_questions()
    audit_summary()

    R.save(OUTPUT_FILE)

    print("=" * 90)
    print("TFT INSIGHT — ROLE INFERENCE DEEP AUDIT")
    print("=" * 90)
    print()
    print("Auditoria concluída.")
    print("Modo: SOMENTE LEITURA")
    print()
    print(f"Relatório:")
    print(OUTPUT_FILE)
    print()
    print("Envie esse TXT no ChatGPT para análise.")
    print("=" * 90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())