from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# ======================================================================================
# TFT INSIGHT
# AUDITORIA ESTRUTURAL DO CARRY DETECTOR
#
# Objetivo:
#   Descobrir o caminho completo da inteligência de carry:
#
#   Riot Match JSON / Static Data
#       -> transformação / normalização
#       -> lógica de identificação/ranking
#       -> contratos / schemas
#       -> análise integrada / API
#       -> Streamlit / UI
#
# IMPORTANTE:
#   - somente leitura;
#   - não importa módulos do projeto;
#   - não executa FastAPI/Streamlit;
#   - não escreve arquivos;
#   - não altera código;
#   - usa AST + busca textual.
# ======================================================================================


AUDIT_VERSION = "1.0"


# --------------------------------------------------------------------------------------
# Diretórios que não devem fazer parte da investigação principal.
# --------------------------------------------------------------------------------------

IGNORED_DIR_NAMES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
}


IGNORED_PATH_PARTS = {
    ("scripts", "archive"),
    ("data", "cache"),
    ("data", "debug"),
    ("data", "diagnostics"),
    ("data", "history"),
    ("data", "players"),
}


SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
}


# --------------------------------------------------------------------------------------
# Grupos de busca
# --------------------------------------------------------------------------------------

PATTERN_GROUPS: dict[str, list[str]] = {
    "CARRY_CORE": [
        r"\bcarry\b",
        r"\bcarries\b",
        r"carry[_\-\s]?item",
        r"carry[_\-\s]?score",
        r"carry[_\-\s]?candidate",
        r"carry[_\-\s]?detector",
        r"primary[_\-\s]?carry",
        r"secondary[_\-\s]?carry",
        r"main[_\-\s]?carry",
        r"identify[_\-\s]?carry",
        r"detect[_\-\s]?carry",
        r"select[_\-\s]?carry",
        r"rank[_\-\s]?carry",
        r"best[_\-\s]?carry",
    ],

    "ITEMIZATION": [
        r"\bitem\b",
        r"\bitems\b",
        r"itemization",
        r"itemisation",
        r"equipped",
        r"equipment",
        r"completed[_\-\s]?item",
        r"full[_\-\s]?item",
        r"radiant",
        r"artifact",
        r"support[_\-\s]?item",
        r"emblem",
    ],

    "UNIT_CHAMPION": [
        r"\bunit\b",
        r"\bunits\b",
        r"\bchampion\b",
        r"\bchampions\b",
        r"character[_\-\s]?id",
        r"character[_\-\s]?name",
        r"champion[_\-\s]?id",
        r"unit[_\-\s]?id",
        r"api[_\-\s]?name",
        r"display[_\-\s]?name",
        r"tft[_\-\s]?unit",
    ],

    "ROLE_ARCHETYPE": [
        r"\brole\b",
        r"\barchetype\b",
        r"\bclass\b",
        r"\bposition\b",
        r"\bfrontline\b",
        r"\bbackline\b",
        r"\btank\b",
        r"\bsupport\b",
        r"\butility\b",
        r"\bcaster\b",
        r"\bfighter\b",
        r"\bassassin\b",
        r"\bmarksman\b",
        r"\bmelee\b",
        r"\branged\b",
    ],

    "COMBAT_IMPACT": [
        r"\bdamage\b",
        r"damage[_\-\s]?dealt",
        r"damage[_\-\s]?taken",
        r"\bdps\b",
        r"\bhealing\b",
        r"\bshield",
        r"\bkill",
        r"\bcombat\b",
        r"\bimpact\b",
    ],

    "STAR_COST": [
        r"star[_\-\s]?level",
        r"\bstars?\b",
        r"\brarity\b",
        r"\btier\b",
        r"\bcost\b",
        r"shop[_\-\s]?cost",
    ],

    "RIOT_MATCH": [
        r"match[_\-\s]?json",
        r"match[_\-\s]?data",
        r"match[_\-\s]?dto",
        r"match[_\-\s]?v1",
        r"match[_\-\s]?history",
        r"\bparticipant",
        r"\bparticipants\b",
        r"\bpuuid\b",
        r"riot",
        r"tft[_\-\s]?match",
        r"riot[_\-\s]?api",
    ],

    "STATIC_DATA": [
        r"data[_\-\s]?dragon",
        r"datadragon",
        r"\bddragon\b",
        r"static[_\-\s]?data",
        r"communitydragon",
        r"community[_\-\s]?dragon",
        r"\bcdragon\b",
        r"set[_\-\s]?data",
        r"champion[_\-\s]?data",
        r"unit[_\-\s]?data",
        r"item[_\-\s]?data",
        r"traits?\.json",
        r"champions?\.json",
        r"items?\.json",
    ],

    "TRAITS": [
        r"\btrait\b",
        r"\btraits\b",
        r"trait[_\-\s]?name",
        r"trait[_\-\s]?style",
        r"synergy",
    ],

    "CONTRACT_SCHEMA": [
        r"\bpydantic\b",
        r"\bBaseModel\b",
        r"\bdataclass\b",
        r"\bTypedDict\b",
        r"\bProtocol\b",
        r"\bschema\b",
        r"\bcontract\b",
        r"\bresponse\b",
        r"\brequest\b",
    ],

    "API": [
        r"\bAPIRouter\b",
        r"\bFastAPI\b",
        r"@router\.",
        r"@app\.",
        r"integrated[_\-\s]?analysis",
        r"analysis[_\-\s]?response",
    ],

    "UI": [
        r"\bstreamlit\b",
        r"\bst\.",
        r"render",
        r"display",
        r"view[_\-\s]?model",
        r"presentation",
        r"coach",
        r"expander",
        r"metric",
        r"markdown",
    ],
}


COMPILED_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    group: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for group, patterns in PATTERN_GROUPS.items()
}


# Palavras mais específicas usadas para definir relevância do arquivo.
STRONG_TERMS = [
    re.compile(x, re.IGNORECASE)
    for x in [
        r"carry_item",
        r"carry_detector",
        r"carry_score",
        r"carry_candidate",
        r"primary_carry",
        r"secondary_carry",
        r"identify_carry",
        r"detect_carry",
        r"select_carry",
        r"rank_carr",
        r"carry analysis",
        r"carry_analysis",
    ]
]


# Campos que queremos localizar explicitamente quando acessados no código.
INTERESTING_FIELD_NAMES = {
    "carry",
    "carries",
    "primary_carry",
    "secondary_carry",
    "main_carry",
    "carry_score",
    "carry_items",
    "carry_item",
    "item",
    "items",
    "item_name",
    "item_names",
    "itemization",
    "character_id",
    "character_name",
    "champion_id",
    "champion_name",
    "unit",
    "units",
    "unit_id",
    "unit_name",
    "tier",
    "rarity",
    "cost",
    "star_level",
    "stars",
    "traits",
    "trait",
    "damage",
    "damage_dealt",
    "damage_taken",
    "healing",
    "shielding",
    "placement",
    "level",
    "participant",
    "participants",
    "puuid",
    "augments",
}


# --------------------------------------------------------------------------------------
# Estruturas
# --------------------------------------------------------------------------------------

@dataclass
class DefinitionInfo:
    file: Path
    line: int
    kind: str
    name: str


@dataclass
class ImportInfo:
    file: Path
    line: int
    module: str


@dataclass
class FieldAccessInfo:
    file: Path
    line: int
    field: str
    expression: str


@dataclass
class FileAudit:
    path: Path
    score: int = 0
    group_counts: dict[str, int] = field(default_factory=dict)
    strong_hits: int = 0
    definitions: list[DefinitionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    field_accesses: list[FieldAccessInfo] = field(default_factory=list)


# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------

def normalize_path(path: Path) -> str:
    return path.as_posix()


def relative_path(path: Path, root: Path) -> str:
    try:
        return normalize_path(path.relative_to(root))
    except ValueError:
        return normalize_path(path)


def is_ignored(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts

    if any(part in IGNORED_DIR_NAMES for part in rel_parts):
        return True

    lowered = tuple(part.lower() for part in rel_parts)

    for ignored_tuple in IGNORED_PATH_PARTS:
        ignored_lower = tuple(part.lower() for part in ignored_tuple)

        for index in range(len(lowered) - len(ignored_lower) + 1):
            if lowered[index:index + len(ignored_lower)] == ignored_lower:
                return True

    return False


def iter_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if is_ignored(path, root):
            continue

        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue

        yield path


def read_text_safely(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return None
    except Exception:
        return None


def clean_line(line: str, max_len: int = 220) -> str:
    line = line.strip().replace("\t", " ")
    line = re.sub(r"\s+", " ", line)

    if len(line) > max_len:
        return line[:max_len - 3] + "..."

    return line


def section(title: str) -> None:
    print()
    print("=" * 120)
    print(title)
    print("=" * 120)


def subsection(title: str) -> None:
    print()
    print("-" * 120)
    print(title)
    print("-" * 120)


# --------------------------------------------------------------------------------------
# AST
# --------------------------------------------------------------------------------------

class PythonStructureVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.definitions: list[DefinitionInfo] = []
        self.imports: list[ImportInfo] = []
        self.field_accesses: list[FieldAccessInfo] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.definitions.append(
            DefinitionInfo(
                file=self.file_path,
                line=node.lineno,
                kind="function",
                name=node.name,
            )
        )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.definitions.append(
            DefinitionInfo(
                file=self.file_path,
                line=node.lineno,
                kind="async function",
                name=node.name,
            )
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.definitions.append(
            DefinitionInfo(
                file=self.file_path,
                line=node.lineno,
                kind="class",
                name=node.name,
            )
        )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    file=self.file_path,
                    line=node.lineno,
                    module=alias.name,
                )
            )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""

        for alias in node.names:
            name = f"{module}.{alias.name}" if module else alias.name

            self.imports.append(
                ImportInfo(
                    file=self.file_path,
                    line=node.lineno,
                    module=name,
                )
            )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.lower() in INTERESTING_FIELD_NAMES:
            self.field_accesses.append(
                FieldAccessInfo(
                    file=self.file_path,
                    line=node.lineno,
                    field=node.attr,
                    expression=safe_unparse(node),
                )
            )

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        field = extract_subscript_key(node)

        if field and field.lower() in INTERESTING_FIELD_NAMES:
            self.field_accesses.append(
                FieldAccessInfo(
                    file=self.file_path,
                    line=node.lineno,
                    field=field,
                    expression=safe_unparse(node),
                )
            )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Detecta padrões como:
        # obj.get("items")
        # dict.get("character_id")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            if node.args:
                first = node.args[0]

                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    field_name = first.value

                    if field_name.lower() in INTERESTING_FIELD_NAMES:
                        self.field_accesses.append(
                            FieldAccessInfo(
                                file=self.file_path,
                                line=node.lineno,
                                field=field_name,
                                expression=safe_unparse(node),
                            )
                        )

        self.generic_visit(node)


def extract_subscript_key(node: ast.Subscript) -> str | None:
    slice_node = node.slice

    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
        return slice_node.value

    return None


def safe_unparse(node: ast.AST) -> str:
    try:
        return clean_line(ast.unparse(node), max_len=180)
    except Exception:
        return "<expression>"


def inspect_python_structure(
    path: Path,
) -> tuple[
    list[DefinitionInfo],
    list[ImportInfo],
    list[FieldAccessInfo],
]:
    text = read_text_safely(path)

    if text is None:
        return [], [], []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], [], []

    visitor = PythonStructureVisitor(path)
    visitor.visit(tree)

    return (
        visitor.definitions,
        visitor.imports,
        visitor.field_accesses,
    )


# --------------------------------------------------------------------------------------
# Relevância
# --------------------------------------------------------------------------------------

def count_group_matches(text: str) -> dict[str, int]:
    result: dict[str, int] = {}

    for group, patterns in COMPILED_PATTERNS.items():
        count = 0

        for pattern in patterns:
            count += len(pattern.findall(text))

        if count:
            result[group] = count

    return result


def count_strong_hits(text: str) -> int:
    return sum(len(pattern.findall(text)) for pattern in STRONG_TERMS)


def calculate_relevance(
    path: Path,
    group_counts: dict[str, int],
    strong_hits: int,
) -> int:
    score = 0

    path_text = normalize_path(path).lower()

    # Carry é o principal sinal.
    score += min(group_counts.get("CARRY_CORE", 0), 20) * 5

    # Strong terms pesam ainda mais.
    score += min(strong_hits, 10) * 10

    # Sinais auxiliares.
    score += min(group_counts.get("ITEMIZATION", 0), 15) * 2
    score += min(group_counts.get("UNIT_CHAMPION", 0), 15) * 2
    score += min(group_counts.get("ROLE_ARCHETYPE", 0), 10) * 2
    score += min(group_counts.get("COMBAT_IMPACT", 0), 10)
    score += min(group_counts.get("STAR_COST", 0), 10)
    score += min(group_counts.get("RIOT_MATCH", 0), 10)
    score += min(group_counts.get("STATIC_DATA", 0), 10)
    score += min(group_counts.get("CONTRACT_SCHEMA", 0), 10)
    score += min(group_counts.get("API", 0), 10)
    score += min(group_counts.get("UI", 0), 10)

    # Caminhos semanticamente relevantes.
    if "carry" in path_text:
        score += 40

    if "item" in path_text:
        score += 10

    if "analysis" in path_text:
        score += 5

    if "integration_engine" in path_text:
        score += 5

    if "contract" in path_text:
        score += 5

    if "route" in path_text or "/api/" in path_text:
        score += 5

    if "streamlit" in path_text or "partner_platform" in path_text:
        score += 5

    return score


# --------------------------------------------------------------------------------------
# Busca de snippets
# --------------------------------------------------------------------------------------

def find_matching_lines(
    path: Path,
    patterns: list[re.Pattern[str]],
    max_results: int = 30,
) -> list[tuple[int, str]]:
    text = read_text_safely(path)

    if text is None:
        return []

    results: list[tuple[int, str]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in patterns):
            results.append((line_number, clean_line(line)))

            if len(results) >= max_results:
                break

    return results


def combined_patterns(groups: list[str]) -> list[re.Pattern[str]]:
    output: list[re.Pattern[str]] = []

    for group in groups:
        output.extend(COMPILED_PATTERNS[group])

    return output


# --------------------------------------------------------------------------------------
# Auditoria
# --------------------------------------------------------------------------------------

def build_audit(root: Path) -> tuple[list[FileAudit], int]:
    audits: list[FileAudit] = []
    total_files = 0

    for path in iter_source_files(root):
        total_files += 1

        text = read_text_safely(path)

        if text is None:
            continue

        group_counts = count_group_matches(text)
        strong_hits = count_strong_hits(text)

        relevant = (
            group_counts.get("CARRY_CORE", 0) > 0
            or strong_hits > 0
            or "carry" in path.name.lower()
        )

        if not relevant:
            continue

        audit = FileAudit(
            path=path,
            group_counts=group_counts,
            strong_hits=strong_hits,
        )

        audit.score = calculate_relevance(
            path,
            group_counts,
            strong_hits,
        )

        if path.suffix.lower() == ".py":
            (
                audit.definitions,
                audit.imports,
                audit.field_accesses,
            ) = inspect_python_structure(path)

        audits.append(audit)

    audits.sort(
        key=lambda item: (
            -item.score,
            normalize_path(item.path).lower(),
        )
    )

    return audits, total_files


# --------------------------------------------------------------------------------------
# Relatório
# --------------------------------------------------------------------------------------

def print_header(root: Path, total_scanned: int, audits: list[FileAudit]) -> None:
    section("TFT INSIGHT — AUDITORIA ESTRUTURAL DO CARRY DETECTOR")

    print(f"Versão da auditoria : {AUDIT_VERSION}")
    print(f"Projeto              : {root}")
    print(f"Arquivos examinados  : {total_scanned}")
    print(f"Arquivos relevantes  : {len(audits)}")
    print("Modo                  : SOMENTE LEITURA")
    print()
    print("Objetivo:")
    print("  Riot/static data -> transformação -> carry detector -> contratos -> API -> UI")


def print_candidate_files(root: Path, audits: list[FileAudit]) -> None:
    section("1. ARQUIVOS ENVOLVIDOS NA INTELIGÊNCIA DE CARRY")

    if not audits:
        print("Nenhuma referência a carry encontrada.")
        return

    for index, audit in enumerate(audits, start=1):
        rel = relative_path(audit.path, root)

        groups = ", ".join(
            f"{name}={count}"
            for name, count in sorted(audit.group_counts.items())
            if count
        )

        print(
            f"[{index:02d}] score={audit.score:03d} "
            f"strong={audit.strong_hits:02d}  {rel}"
        )

        if groups:
            print(f"     sinais: {groups}")


def print_carry_definitions(root: Path, audits: list[FileAudit]) -> None:
    section("2. FUNÇÕES / CLASSES POTENCIALMENTE RESPONSÁVEIS PELO CARRY")

    patterns = [
        re.compile(
            r"(carry|item|champion|unit|rank|score|select|detect|identify|candidate)",
            re.IGNORECASE,
        )
    ]

    found = 0

    for audit in audits:
        for definition in audit.definitions:
            if not any(pattern.search(definition.name) for pattern in patterns):
                continue

            found += 1

            print(
                f"{relative_path(definition.file, root)}:"
                f"{definition.line}  "
                f"{definition.kind:<14} {definition.name}"
            )

    if not found:
        print("Nenhuma definição com nome diretamente relacionado encontrada.")


def print_field_accesses(root: Path, audits: list[FileAudit]) -> None:
    section("3. CAMPOS USADOS NA LÓGICA DE CARRY / ITEMIZAÇÃO")

    grouped: dict[str, list[FieldAccessInfo]] = defaultdict(list)

    for audit in audits:
        for info in audit.field_accesses:
            grouped[info.field].append(info)

    if not grouped:
        print("Nenhum acesso explícito aos campos monitorados foi encontrado via AST.")
        return

    for field_name in sorted(grouped):
        infos = grouped[field_name]

        print()
        print(f"[{field_name}] — {len(infos)} acesso(s)")

        for info in infos[:20]:
            print(
                f"  {relative_path(info.file, root)}:{info.line}"
                f" -> {info.expression}"
            )

        if len(infos) > 20:
            print(f"  ... +{len(infos) - 20} acesso(s)")


def print_carry_snippets(root: Path, audits: list[FileAudit]) -> None:
    section("4. TRECHOS DIRETAMENTE RELACIONADOS À ESCOLHA/RANKING DO CARRY")

    patterns = combined_patterns(
        [
            "CARRY_CORE",
            "ITEMIZATION",
        ]
    )

    shown_files = 0

    for audit in audits[:25]:
        hits = find_matching_lines(
            audit.path,
            patterns,
            max_results=18,
        )

        if not hits:
            continue

        shown_files += 1

        subsection(relative_path(audit.path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")

    if not shown_files:
        print("Nenhum trecho encontrado.")


def print_dependencies(root: Path, audits: list[FileAudit]) -> None:
    section("5. DEPENDÊNCIAS / IMPORTS DOS ARQUIVOS DE CARRY")

    seen: set[tuple[str, str]] = set()
    found = 0

    relevant_module_regex = re.compile(
        r"(carry|item|riot|match|champion|unit|static|dragon|analysis|contract|schema|integration)",
        re.IGNORECASE,
    )

    for audit in audits[:30]:
        for import_info in audit.imports:
            key = (
                relative_path(import_info.file, root),
                import_info.module,
            )

            if key in seen:
                continue

            seen.add(key)

            if not relevant_module_regex.search(import_info.module):
                continue

            found += 1

            print(
                f"{relative_path(import_info.file, root)}:"
                f"{import_info.line} -> {import_info.module}"
            )

    if not found:
        print("Nenhuma dependência semanticamente relacionada encontrada.")


def print_contracts(root: Path, audits: list[FileAudit]) -> None:
    section("6. CONTRATOS / SCHEMAS ENVOLVIDOS")

    patterns = combined_patterns(
        [
            "CARRY_CORE",
            "CONTRACT_SCHEMA",
        ]
    )

    candidates = [
        audit
        for audit in audits
        if (
            "contract" in normalize_path(audit.path).lower()
            or "schema" in normalize_path(audit.path).lower()
            or audit.group_counts.get("CONTRACT_SCHEMA", 0)
        )
    ]

    if not candidates:
        print("Nenhum contrato/schema relacionado diretamente identificado.")
        return

    for audit in candidates[:25]:
        hits = find_matching_lines(
            audit.path,
            patterns,
            max_results=20,
        )

        if not hits:
            continue

        subsection(relative_path(audit.path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_riot_json(root: Path, audits: list[FileAudit]) -> None:
    section("7. USO DE RIOT MATCH JSON / PARTICIPANT / UNITS")

    patterns = combined_patterns(
        [
            "RIOT_MATCH",
            "UNIT_CHAMPION",
            "ITEMIZATION",
            "STAR_COST",
            "TRAITS",
            "COMBAT_IMPACT",
        ]
    )

    candidates = [
        audit
        for audit in audits
        if audit.group_counts.get("RIOT_MATCH", 0) > 0
    ]

    if not candidates:
        print("Nenhuma ligação explícita com Riot Match JSON encontrada nos arquivos de carry.")
        return

    for audit in candidates[:20]:
        subsection(relative_path(audit.path, root))

        hits = find_matching_lines(
            audit.path,
            patterns,
            max_results=30,
        )

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_static_data(root: Path, audits: list[FileAudit]) -> None:
    section("8. DATA DRAGON / COMMUNITYDRAGON / STATIC DATA")

    # Aqui fazemos busca global, porque static data pode morar em um arquivo
    # que nunca menciona a palavra "carry".
    patterns = combined_patterns(
        [
            "STATIC_DATA",
            "ROLE_ARCHETYPE",
            "UNIT_CHAMPION",
        ]
    )

    candidates: list[tuple[Path, list[tuple[int, str]]]] = []

    for path in iter_source_files(root):
        hits = find_matching_lines(
            path,
            patterns,
            max_results=20,
        )

        if not hits:
            continue

        text = read_text_safely(path) or ""

        static_score = sum(
            len(pattern.findall(text))
            for pattern in COMPILED_PATTERNS["STATIC_DATA"]
        )

        role_score = sum(
            len(pattern.findall(text))
            for pattern in COMPILED_PATTERNS["ROLE_ARCHETYPE"]
        )

        if static_score == 0 and role_score == 0:
            continue

        candidates.append((path, hits))

    candidates.sort(
        key=lambda item: normalize_path(item[0]).lower()
    )

    if not candidates:
        print("Nenhuma referência clara a Data Dragon/static data/role encontrada.")
        return

    for path, hits in candidates[:30]:
        subsection(relative_path(path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_mappings(root: Path) -> None:
    section("9. POSSÍVEIS MAPPINGS DE CHAMPION / UNIT / ITEM / ROLE")

    mapping_patterns = [
        re.compile(
            r"(champion|unit|item|carry|role|archetype|tank|support|frontline|backline)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(mapping|map_|_map\b|lookup|dictionary|aliases|metadata)",
            re.IGNORECASE,
        ),
    ]

    candidates: list[tuple[Path, list[tuple[int, str]]]] = []

    for path in iter_source_files(root):
        text = read_text_safely(path)

        if text is None:
            continue

        # Precisa possuir algum conceito de unidade/item/role.
        if not mapping_patterns[0].search(text):
            continue

        # E algum sinal de estrutura de mapping.
        if not (
            mapping_patterns[1].search(text)
            or path.suffix.lower() == ".json"
        ):
            continue

        hits: list[tuple[int, str]] = []

        for line_number, line in enumerate(text.splitlines(), start=1):
            if (
                mapping_patterns[0].search(line)
                or mapping_patterns[1].search(line)
            ):
                hits.append((line_number, clean_line(line)))

                if len(hits) >= 20:
                    break

        if hits:
            candidates.append((path, hits))

    if not candidates:
        print("Nenhum mapping candidato encontrado.")
        return

    for path, hits in candidates[:30]:
        subsection(relative_path(path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_api_flow(root: Path) -> None:
    section("10. CAMINHO DO RESULTADO ATÉ A API")

    patterns = combined_patterns(
        [
            "CARRY_CORE",
            "API",
            "CONTRACT_SCHEMA",
        ]
    )

    candidates: list[tuple[Path, list[tuple[int, str]]]] = []

    for path in iter_source_files(root):
        path_lower = normalize_path(path).lower()

        if path.suffix.lower() != ".py":
            continue

        text = read_text_safely(path)

        if text is None:
            continue

        if not re.search(r"\bcarry\b", text, re.IGNORECASE):
            continue

        api_like = (
            "/api/" in path_lower
            or "/routes/" in path_lower
            or "integrated_analysis" in path_lower
            or "pipeline" in path_lower
            or re.search(r"(APIRouter|FastAPI|IntegratedAnalysis)", text)
        )

        if not api_like:
            continue

        hits = find_matching_lines(
            path,
            patterns,
            max_results=30,
        )

        if hits:
            candidates.append((path, hits))

    if not candidates:
        print("Nenhum caminho API relacionado encontrado.")
        return

    for path, hits in candidates[:30]:
        subsection(relative_path(path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_ui_flow(root: Path) -> None:
    section("11. CAMINHO DO RESULTADO ATÉ STREAMLIT / UI")

    carry_regex = re.compile(
        r"\b(carry|carries|carry_item|primary_carry|secondary_carry)\b",
        re.IGNORECASE,
    )

    ui_regex = re.compile(
        r"(streamlit|\bst\.|render|markdown|metric|expander|caption|write|presentation)",
        re.IGNORECASE,
    )

    candidates: list[tuple[Path, list[tuple[int, str]]]] = []

    for path in iter_source_files(root):
        if path.suffix.lower() != ".py":
            continue

        text = read_text_safely(path)

        if text is None:
            continue

        if not carry_regex.search(text):
            continue

        path_lower = normalize_path(path).lower()

        ui_like = (
            "streamlit" in path_lower
            or "partner_platform" in path_lower
            or "/pages/" in path_lower
            or "/ui/" in path_lower
            or "/components/" in path_lower
            or ui_regex.search(text)
        )

        if not ui_like:
            continue

        hits: list[tuple[int, str]] = []

        for line_number, line in enumerate(text.splitlines(), start=1):
            if carry_regex.search(line) or ui_regex.search(line):
                hits.append((line_number, clean_line(line)))

                if len(hits) >= 35:
                    break

        if hits:
            candidates.append((path, hits))

    if not candidates:
        print("Nenhum consumidor de carry na UI identificado.")
        return

    for path, hits in candidates[:30]:
        subsection(relative_path(path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_role_signals(root: Path) -> None:
    section("12. SINAIS EXISTENTES DE ROLE / TANK / FRONTLINE / BACKLINE")

    patterns = combined_patterns(
        [
            "ROLE_ARCHETYPE",
            "COMBAT_IMPACT",
        ]
    )

    candidates: list[tuple[Path, list[tuple[int, str]]]] = []

    for path in iter_source_files(root):
        text = read_text_safely(path)

        if text is None:
            continue

        role_hits = sum(
            len(pattern.findall(text))
            for pattern in COMPILED_PATTERNS["ROLE_ARCHETYPE"]
        )

        if role_hits == 0:
            continue

        hits = find_matching_lines(
            path,
            patterns,
            max_results=25,
        )

        if hits:
            candidates.append((path, hits))

    if not candidates:
        print("Nenhum sinal explícito de role/archetype/frontline/tank encontrado.")
        return

    for path, hits in candidates[:30]:
        subsection(relative_path(path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")


def print_suspicious_heuristics(root: Path, audits: list[FileAudit]) -> None:
    section("13. HEURÍSTICAS POTENCIALMENTE IMPORTANTES / SUSPEITAS")

    heuristic_patterns = [
        re.compile(r"\blen\s*\([^)]*items", re.IGNORECASE),
        re.compile(r"items?.*(score|count|len|weight)", re.IGNORECASE),
        re.compile(r"(score|weight).*(items?|stars?|cost|tier)", re.IGNORECASE),
        re.compile(r"(sorted|sort|max|min)\s*\(", re.IGNORECASE),
        re.compile(r"reverse\s*=\s*True", re.IGNORECASE),
        re.compile(r"\btop[_\-\s]?\d", re.IGNORECASE),
        re.compile(r"\bfirst\b", re.IGNORECASE),
        re.compile(r"\bprimary\b", re.IGNORECASE),
        re.compile(r"\bsecondary\b", re.IGNORECASE),
        re.compile(r"\bthreshold\b", re.IGNORECASE),
        re.compile(r"\bconfidence\b", re.IGNORECASE),
        re.compile(r"\bweight\b", re.IGNORECASE),
        re.compile(r"\bscore\b", re.IGNORECASE),
    ]

    found = 0

    for audit in audits[:30]:
        text = read_text_safely(audit.path)

        if text is None:
            continue

        hits: list[tuple[int, str]] = []

        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in heuristic_patterns):
                hits.append((line_number, clean_line(line)))

                if len(hits) >= 25:
                    break

        if not hits:
            continue

        found += 1

        subsection(relative_path(audit.path, root))

        for line_number, line in hits:
            print(f"{line_number:5d}: {line}")

    if not found:
        print("Nenhuma heurística candidata encontrada.")


def print_static_json_candidates(root: Path) -> None:
    section("14. ARQUIVOS JSON/YAML POTENCIALMENTE ÚTEIS AO CARRY DETECTOR V2")

    candidate_name_regex = re.compile(
        r"(champ|unit|item|trait|set|tft|static|metadata|dragon)",
        re.IGNORECASE,
    )

    candidates: list[Path] = []

    for path in iter_source_files(root):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue

        if candidate_name_regex.search(path.name):
            candidates.append(path)

    if not candidates:
        print("Nenhum arquivo estático candidato encontrado pelo nome.")
        return

    for path in sorted(candidates, key=lambda p: normalize_path(p).lower())[:100]:
        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        print(
            f"{relative_path(path, root):<90} "
            f"{size:>12,} bytes"
        )


def print_summary(root: Path, audits: list[FileAudit]) -> None:
    section("15. RESUMO PARA ANÁLISE DO CARRY DETECTOR V2")

    print("Arquivos de maior relevância estrutural:")

    for audit in audits[:15]:
        print(
            f"  score={audit.score:03d}  "
            f"{relative_path(audit.path, root)}"
        )

    print()
    print("Ao analisar este relatório, queremos responder:")
    print()
    print("  [A] Onde nasce a informação de units/items?")
    print("  [B] Qual estrutura representa cada unidade da partida?")
    print("  [C] Qual função decide que uma unidade é carry?")
    print("  [D] Essa decisão usa quantidade de itens como sinal dominante?")
    print("  [E] Usa star_level/cost/tier?")
    print("  [F] Usa dano ou algum indicador real de impacto?")
    print("  [G] Existe informação de role/archetype?")
    print("  [H] Existe static data além do Riot Match JSON?")
    print("  [I] Existem mappings manuais de champion/unit/item?")
    print("  [J] O sistema força sempre um carry?")
    print("  [K] Existe confidence/threshold?")
    print("  [L] Onde o carry entra no contrato integrado?")
    print("  [M] Onde a UI consome e apresenta esse resultado?")
    print()
    print("Nenhuma alteração foi realizada pelo script.")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def discover_project_root(explicit_root: str | None) -> Path:
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()

        if not root.exists():
            raise FileNotFoundError(
                f"Diretório informado não existe: {root}"
            )

        return root

    current = Path.cwd().resolve()

    markers = {
        "src",
        "scripts",
    }

    for candidate in [current, *current.parents]:
        present = {
            child.name
            for child in candidate.iterdir()
            if child.exists()
        }

        if markers.issubset(present):
            return candidate

    return current


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Auditoria estrutural somente leitura do Carry Detector "
            "do TFT Insight."
        )
    )

    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Raiz do projeto. Padrão: descoberta automática.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        root = discover_project_root(args.root)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    audits, total_scanned = build_audit(root)

    print_header(
        root=root,
        total_scanned=total_scanned,
        audits=audits,
    )

    print_candidate_files(root, audits)
    print_carry_definitions(root, audits)
    print_field_accesses(root, audits)
    print_carry_snippets(root, audits)
    print_dependencies(root, audits)
    print_contracts(root, audits)
    print_riot_json(root, audits)
    print_static_data(root, audits)
    print_mappings(root)
    print_api_flow(root)
    print_ui_flow(root)
    print_role_signals(root)
    print_suspicious_heuristics(root, audits)
    print_static_json_candidates(root)
    print_summary(root, audits)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())