from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


# ======================================================================================
# TFT INSIGHT
# AUDITORIA — FONTES DE DADOS PARA UNIT ROLE INTELLIGENCE V2
#
# Objetivo:
#
#   Descobrir quais sinais REAIS estão disponíveis para classificar:
#
#       primary damage carry
#       secondary damage carry
#       main tank
#       secondary tank
#       support / utility
#       hybrid
#       unknown
#
# Fontes auditadas:
#
#   1. Riot Match JSON salvo localmente
#   2. ParticipantSnapshot / UnitSnapshot
#   3. CommunityDragon
#   4. Data Dragon / static data local
#   5. UnitRoleSeedInference
#   6. MetadataItemClassifier
#   7. StatisticalItemClassifier
#   8. HybridItemClassifier
#   9. ItemObservationCollector
#  10. CommunityDragonItemParser
#
# IMPORTANTE:
#
#   - não chama Riot API;
#   - não altera arquivos do produto;
#   - não importa código do projeto;
#   - não inicia API;
#   - não inicia Streamlit;
#   - não executa classificadores;
#   - somente lê arquivos e AST;
#   - grava apenas o relatório TXT.
#
# ======================================================================================


AUDIT_VERSION = "1.0"

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_FILE = ROOT / "role_v2_data_sources_audit.txt"


# ======================================================================================
# Caminhos prioritários
# ======================================================================================


ROLE_FILES = [
    ROOT / "src/role_inference/services/unit_role_seed_inference.py",
    ROOT / "src/role_inference/services/metadata_item_classifier.py",
    ROOT / "src/role_inference/services/hybrid_item_classifier.py",
    ROOT / "src/role_inference/services/statistical_item_classifier.py",
    ROOT / "src/role_inference/services/item_catalog_classifier.py",
    ROOT / "src/role_inference/services/item_observation_collector.py",
    ROOT / "src/role_inference/services/community_dragon_item_parser.py",
    ROOT / "src/role_inference/clients/community_dragon_client.py",
    ROOT / "src/role_inference/services/role_inference_engine.py",
]


MODEL_FILES = [
    ROOT / "src/performance_engine/models/unit_snapshot.py",
    ROOT / "src/performance_engine/models/participant_snapshot.py",
    ROOT / "src/role_inference/models/rich_item_data.py",
    ROOT / "src/role_inference/models/item_classification.py",
    ROOT / "src/role_inference/models/item_observation.py",
    ROOT / "src/role_inference/models/role_seed_assessment.py",
    ROOT / "src/role_inference/models/unit_role_seed.py",
]


STATIC_ROOT = ROOT / "data/static_data"

ROLE_DATA_ROOT = ROOT / "data/role_inference"


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


# ======================================================================================
# Reporter
# ======================================================================================


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


# ======================================================================================
# Helpers
# ======================================================================================


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except Exception:
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


def clean(value: str, max_len: int = 350) -> str:
    value = value.rstrip().replace("\t", "    ")

    if len(value) > max_len:
        return value[: max_len - 3] + "..."

    return value


def load_json(path: Path) -> Any | None:
    text = read_text(path)

    if text is None:
        return None

    try:
        return json.loads(text)
    except Exception:
        return None


def iter_project_python() -> Iterable[Path]:
    for path in ROOT.rglob("*.py"):
        rel = relative(path)

        if any(
            ignored in rel
            for ignored in IGNORED_DIRS
        ):
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


# ======================================================================================
# AST helpers
# ======================================================================================


@dataclass
class Definition:
    name: str
    kind: str
    start: int
    end: int


def definitions(path: Path) -> list[Definition]:
    tree = parse_python(path)

    if tree is None:
        return []

    output: list[Definition] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            output.append(
                Definition(
                    node.name,
                    "class",
                    node.lineno,
                    getattr(node, "end_lineno", node.lineno),
                )
            )

        elif isinstance(node, ast.FunctionDef):
            output.append(
                Definition(
                    node.name,
                    "function",
                    node.lineno,
                    getattr(node, "end_lineno", node.lineno),
                )
            )

    return sorted(
        output,
        key=lambda item: item.start,
    )


def print_definition(path: Path, definition: Definition) -> None:
    lines = (read_text(path) or "").splitlines()

    for number in range(
        definition.start,
        min(definition.end, len(lines)) + 1,
    ):
        R.write(
            f"{number:5d}: {clean(lines[number - 1])}"
        )


# ======================================================================================
# JSON introspection
# ======================================================================================


def walk_json(
    value: Any,
    *,
    prefix: str = "",
    fields: Counter[str] | None = None,
    types: dict[str, Counter[str]] | None = None,
    examples: dict[str, list[str]] | None = None,
    depth: int = 0,
    max_depth: int = 12,
) -> None:
    if fields is None:
        fields = Counter()

    if types is None:
        types = defaultdict(Counter)

    if examples is None:
        examples = defaultdict(list)

    if depth > max_depth:
        return

    if isinstance(value, dict):
        for key, child in value.items():
            name = str(key)

            field_path = (
                f"{prefix}.{name}"
                if prefix
                else name
            )

            fields[field_path] += 1
            types[field_path][type(child).__name__] += 1

            if (
                len(examples[field_path]) < 3
                and not isinstance(child, (dict, list))
            ):
                examples[field_path].append(
                    clean(repr(child), max_len=120)
                )

            walk_json(
                child,
                prefix=field_path,
                fields=fields,
                types=types,
                examples=examples,
                depth=depth + 1,
                max_depth=max_depth,
            )

    elif isinstance(value, list):
        for child in value[:100]:
            walk_json(
                child,
                prefix=prefix,
                fields=fields,
                types=types,
                examples=examples,
                depth=depth + 1,
                max_depth=max_depth,
            )


# ======================================================================================
# 1. Arquivos
# ======================================================================================


def audit_files() -> None:
    R.section("1. FONTES E MÓDULOS DISPONÍVEIS")

    for path in ROLE_FILES + MODEL_FILES:
        R.write(
            f"{'OK' if path.exists() else 'AUSENTE':<10} "
            f"{relative(path)}"
        )

    R.write()
    R.write(
        f"STATIC_ROOT         : "
        f"{'OK' if STATIC_ROOT.exists() else 'AUSENTE'} "
        f"{relative(STATIC_ROOT)}"
    )

    R.write(
        f"ROLE_DATA_ROOT      : "
        f"{'OK' if ROLE_DATA_ROOT.exists() else 'AUSENTE'} "
        f"{relative(ROLE_DATA_ROOT)}"
    )


# ======================================================================================
# 2. Código completo dos módulos críticos
# ======================================================================================


def audit_role_sources() -> None:
    R.section("2. CÓDIGO DOS MÓDULOS CRÍTICOS")

    for path in ROLE_FILES:
        if not path.exists():
            continue

        R.subsection(relative(path))

        text = read_text(path) or ""

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            R.write(
                f"{number:5d}: {clean(line)}"
            )


# ======================================================================================
# 3. Modelos
# ======================================================================================


def audit_models() -> None:
    R.section("3. MODELOS DE DADOS")

    for path in MODEL_FILES:
        if not path.exists():
            continue

        R.subsection(relative(path))

        text = read_text(path) or ""

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            R.write(
                f"{number:5d}: {clean(line)}"
            )


# ======================================================================================
# 4. Sinais usados por UnitRoleSeedInference
# ======================================================================================


def audit_seed_inference() -> None:
    R.section("4. UNIT ROLE SEED INFERENCE — SINAIS E FÓRMULAS")

    path = (
        ROOT
        / "src/role_inference/services/unit_role_seed_inference.py"
    )

    if not path.exists():
        R.write("Arquivo não encontrado.")
        return

    tree = parse_python(path)

    if tree is None:
        R.write("Não foi possível analisar AST.")
        return

    score_terms = re.compile(
        r"(offense|defense|utility|frontline|backline|"
        r"carry|tank|support|item|tier|rarity|"
        r"confidence|margin|threshold|bonus|penalty)",
        re.IGNORECASE,
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            source = safe_unparse(node)

            if score_terms.search(source):
                R.write(
                    f"{getattr(node, 'lineno', 0):5d}: "
                    f"{clean(source, max_len=500)}"
                )


# ======================================================================================
# 5. Mappings / palavras-chave do MetadataItemClassifier
# ======================================================================================


def audit_metadata_classifier_rules() -> None:
    R.section("5. METADATA ITEM CLASSIFIER — REGRAS / PALAVRAS-CHAVE")

    path = (
        ROOT
        / "src/role_inference/services/metadata_item_classifier.py"
    )

    if not path.exists():
        R.write("Arquivo não encontrado.")
        return

    text = read_text(path) or ""

    regex = re.compile(
        r"(OFFENSE|DEFENSE|UTILITY|offense|defense|utility|"
        r"damage|attack|crit|mana|health|armor|magic|"
        r"shield|heal|stun|slow|control|controle|"
        r"speed|range|ap|ad|tank|support)",
        re.IGNORECASE,
    )

    for number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        if regex.search(line):
            R.write(
                f"{number:5d}: {clean(line)}"
            )


# ======================================================================================
# 6. Hybrid classifier
# ======================================================================================


def audit_hybrid_classifier() -> None:
    R.section("6. HYBRID ITEM CLASSIFIER — COMO COMBINA METADATA + ESTATÍSTICA")

    path = (
        ROOT
        / "src/role_inference/services/hybrid_item_classifier.py"
    )

    if not path.exists():
        R.write("Arquivo não encontrado.")
        return

    text = read_text(path) or ""

    for number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        R.write(
            f"{number:5d}: {clean(line)}"
        )


# ======================================================================================
# 7. Busca Riot Match JSON real
# ======================================================================================


def riot_json_candidates() -> list[Path]:
    candidates: list[Path] = []

    preferred_roots = [
        ROOT / "data/role_inference",
        ROOT / "data",
    ]

    seen: set[Path] = set()

    for base in preferred_roots:
        if not base.exists():
            continue

        for path in base.rglob("*.json"):
            if path in seen:
                continue

            seen.add(path)

            rel = relative(path).lower()

            if (
                "static_data" in rel
                or "cache" in rel
                or "debug" in rel
                or "diagnostic" in rel
            ):
                continue

            text = read_text(path)

            if text is None:
                continue

            sample = text[:50000].lower()

            riot_signals = (
                '"participants"',
                '"puuid"',
                '"units"',
                '"placement"',
                '"traits"',
            )

            if sum(
                signal in sample
                for signal in riot_signals
            ) >= 3:
                candidates.append(path)

    return candidates


def audit_riot_json_files() -> list[Path]:
    R.section("7. RIOT MATCH JSONS REAIS ENCONTRADOS")

    candidates = riot_json_candidates()

    if not candidates:
        R.write(
            "Nenhum JSON local com estrutura clara de Riot Match encontrado."
        )
        return []

    candidates.sort()

    R.write(
        f"Arquivos candidatos encontrados: {len(candidates)}"
    )

    for path in candidates[:100]:
        try:
            size = path.stat().st_size
        except Exception:
            size = 0

        R.write(
            f"{relative(path):<100} {size:>12,} bytes"
        )

    return candidates


# ======================================================================================
# 8. Schema real Riot
# ======================================================================================


def audit_riot_schema(candidates: list[Path]) -> None:
    R.section("8. CAMPOS REAIS DO RIOT MATCH JSON")

    if not candidates:
        R.write("Sem Riot JSON para analisar.")
        return

    # Até 20 partidas para não explodir o relatório.
    selected = candidates[:20]

    fields: Counter[str] = Counter()
    types: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)

    parsed_count = 0

    for path in selected:
        payload = load_json(path)

        if payload is None:
            continue

        parsed_count += 1

        walk_json(
            payload,
            fields=fields,
            types=types,
            examples=examples,
        )

    R.write(
        f"JSONs parseados para schema: {parsed_count}"
    )

    interesting_regex = re.compile(
        r"(participant|unit|item|trait|damage|"
        r"health|mana|attack|armor|magic|"
        r"range|tier|rarity|star|cost|"
        r"placement|position|row|column|"
        r"character|champion|name)",
        re.IGNORECASE,
    )

    interesting = [
        (field_name, count)
        for field_name, count in fields.items()
        if interesting_regex.search(field_name)
    ]

    interesting.sort(
        key=lambda item: (
            item[0].count("."),
            item[0].lower(),
        )
    )

    for field_name, count in interesting:
        type_info = ", ".join(
            f"{name}:{amount}"
            for name, amount
            in types[field_name].most_common()
        )

        sample = (
            ", ".join(examples[field_name])
            if examples[field_name]
            else "-"
        )

        R.write(
            f"{field_name:<90} "
            f"occ={count:<6} "
            f"type={type_info:<24} "
            f"sample={sample}"
        )


# ======================================================================================
# 9. Exemplo real de participant.units
# ======================================================================================


def find_first_participant_units(value: Any) -> list[Any] | None:
    if isinstance(value, dict):
        if (
            "units" in value
            and isinstance(value["units"], list)
            and (
                "placement" in value
                or "puuid" in value
            )
        ):
            return value["units"]

        for child in value.values():
            result = find_first_participant_units(child)

            if result is not None:
                return result

    elif isinstance(value, list):
        for child in value:
            result = find_first_participant_units(child)

            if result is not None:
                return result

    return None


def audit_real_units(candidates: list[Path]) -> None:
    R.section("9. EXEMPLOS REAIS DE UNIT PAYLOAD DA RIOT")

    shown = 0

    for path in candidates:
        payload = load_json(path)

        if payload is None:
            continue

        units = find_first_participant_units(payload)

        if not units:
            continue

        R.subsection(relative(path))

        for index, unit in enumerate(units[:12], start=1):
            R.write(
                f"UNIT {index}:"
            )

            if isinstance(unit, dict):
                for key, value in unit.items():
                    R.write(
                        f"  {key:<35} "
                        f"{clean(repr(value), max_len=500)}"
                    )
            else:
                R.write(
                    f"  {clean(repr(unit), max_len=500)}"
                )

            R.write()

        shown += 1

        if shown >= 3:
            break

    if shown == 0:
        R.write(
            "Nenhum participant.units utilizável encontrado."
        )


# ======================================================================================
# 10. Static JSONs
# ======================================================================================


def static_json_candidates() -> list[Path]:
    if not STATIC_ROOT.exists():
        return []

    regex = re.compile(
        r"(champ|unit|item|trait|tft|community)",
        re.IGNORECASE,
    )

    output: list[Path] = []

    for path in STATIC_ROOT.rglob("*.json"):
        if regex.search(path.name):
            output.append(path)

    return sorted(output)


def audit_static_files() -> list[Path]:
    R.section("10. STATIC DATA TFT DISPONÍVEL")

    files = static_json_candidates()

    if not files:
        R.write("Nenhum static JSON encontrado.")
        return []

    for path in files[:150]:
        try:
            size = path.stat().st_size
        except Exception:
            size = 0

        R.write(
            f"{relative(path):<100} "
            f"{size:>12,} bytes"
        )

    return files


# ======================================================================================
# 11. Schema static data
# ======================================================================================


def audit_static_schema(files: list[Path]) -> None:
    R.section("11. CAMPOS POTENCIALMENTE ÚTEIS NO STATIC DATA")

    wanted = re.compile(
        r"(api.?name|name|display|cost|price|rarity|tier|"
        r"role|archetype|range|attack.?range|"
        r"health|hp|mana|armor|mr|magic.?resist|"
        r"attack.?damage|ad|ability.?power|ap|"
        r"attack.?speed|crit|dodge|"
        r"trait|traits|spell|ability|"
        r"stats|effect|effects|"
        r"position|frontline|backline)",
        re.IGNORECASE,
    )

    for path in files[:40]:
        payload = load_json(path)

        if payload is None:
            continue

        fields: Counter[str] = Counter()
        types: dict[str, Counter[str]] = defaultdict(Counter)
        examples: dict[str, list[str]] = defaultdict(list)

        walk_json(
            payload,
            fields=fields,
            types=types,
            examples=examples,
        )

        matches = [
            (field, count)
            for field, count in fields.items()
            if wanted.search(field)
        ]

        if not matches:
            continue

        R.subsection(relative(path))

        matches.sort(
            key=lambda item: (
                item[0].count("."),
                item[0].lower(),
            )
        )

        for field_name, count in matches[:160]:
            sample = (
                ", ".join(examples[field_name])
                if examples[field_name]
                else "-"
            )

            R.write(
                f"{field_name:<85} "
                f"occ={count:<7} "
                f"sample={sample}"
            )


# ======================================================================================
# 12. Busca por champion/unit metadata
# ======================================================================================


def audit_unit_metadata_examples(files: list[Path]) -> None:
    R.section("12. EXEMPLOS DE METADATA DE CHAMPION / UNIT")

    unit_markers = {
        "apiName",
        "name",
        "cost",
        "traits",
        "stats",
    }

    shown = 0

    def find_unit_dicts(value: Any) -> Iterable[dict[str, Any]]:
        if isinstance(value, dict):
            keys = set(value)

            if len(keys & unit_markers) >= 3:
                yield value

            for child in value.values():
                yield from find_unit_dicts(child)

        elif isinstance(value, list):
            for child in value[:5000]:
                yield from find_unit_dicts(child)

    for path in files:
        payload = load_json(path)

        if payload is None:
            continue

        candidates = list(find_unit_dicts(payload))

        if not candidates:
            continue

        R.subsection(relative(path))

        for candidate in candidates[:5]:
            wanted_keys = [
                key
                for key in candidate
                if re.search(
                    r"(api|name|cost|rarity|tier|trait|"
                    r"stat|range|health|mana|armor|"
                    r"attack|magic|spell|ability)",
                    str(key),
                    re.IGNORECASE,
                )
            ]

            for key in wanted_keys:
                R.write(
                    f"  {key:<30} "
                    f"{clean(repr(candidate[key]), max_len=650)}"
                )

            R.write()

            shown += 1

        if shown >= 20:
            break

    if shown == 0:
        R.write(
            "Nenhum objeto de unidade/champion identificado automaticamente."
        )


# ======================================================================================
# 13. Role/archetype explícito
# ======================================================================================


def audit_explicit_roles(files: list[Path]) -> None:
    R.section("13. ROLE / ARCHETYPE EXPLÍCITO NO STATIC DATA")

    patterns = [
        re.compile(r'"role"\s*:', re.IGNORECASE),
        re.compile(r'"roles"\s*:', re.IGNORECASE),
        re.compile(r'"archetype"\s*:', re.IGNORECASE),
        re.compile(r'"frontline"\s*:', re.IGNORECASE),
        re.compile(r'"backline"\s*:', re.IGNORECASE),
        re.compile(r'"position"\s*:', re.IGNORECASE),
        re.compile(r'"attackRange"\s*:', re.IGNORECASE),
        re.compile(r'"attack_range"\s*:', re.IGNORECASE),
    ]

    total_hits = 0

    for path in files:
        text = read_text(path)

        if text is None:
            continue

        hits: list[tuple[int, str]] = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if any(pattern.search(line) for pattern in patterns):
                hits.append(
                    (number, clean(line, max_len=600))
                )

                if len(hits) >= 30:
                    break

        if not hits:
            continue

        total_hits += len(hits)

        R.subsection(relative(path))

        for number, line in hits:
            R.write(
                f"{number:5d}: {line}"
            )

    if total_hits == 0:
        R.write(
            "Nenhum campo role/archetype/position explícito encontrado "
            "pela busca textual."
        )


# ======================================================================================
# 14. Stats disponíveis
# ======================================================================================


def audit_stats(files: list[Path]) -> None:
    R.section("14. STATS DE UNIDADE DISPONÍVEIS")

    stat_terms = [
        "health",
        "hp",
        "mana",
        "armor",
        "magicResist",
        "magic_resist",
        "attackDamage",
        "attack_damage",
        "attackSpeed",
        "attack_speed",
        "attackRange",
        "attack_range",
        "critChance",
        "crit_chance",
        "abilityPower",
        "ability_power",
    ]

    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    for path in files:
        payload = load_json(path)

        if payload is None:
            continue

        fields: Counter[str] = Counter()
        types: dict[str, Counter[str]] = defaultdict(Counter)
        local_examples: dict[str, list[str]] = defaultdict(list)

        walk_json(
            payload,
            fields=fields,
            types=types,
            examples=local_examples,
        )

        for field_name, amount in fields.items():
            lower = field_name.lower()

            for stat in stat_terms:
                if stat.lower() in lower:
                    counts[field_name] += amount

                    for value in local_examples[field_name]:
                        if len(examples[field_name]) < 5:
                            examples[field_name].append(value)

    if not counts:
        R.write(
            "Nenhum stat de unidade encontrado pelos nomes pesquisados."
        )
        return

    for field_name, count in counts.most_common():
        sample = ", ".join(examples[field_name]) or "-"

        R.write(
            f"{field_name:<90} "
            f"occ={count:<7} "
            f"sample={sample}"
        )


# ======================================================================================
# 15. Traits disponíveis no Riot vs static
# ======================================================================================


def audit_traits(candidates: list[Path], static_files: list[Path]) -> None:
    R.section("15. TRAITS — RIOT MATCH VS STATIC DATA")

    riot_trait_fields: Counter[str] = Counter()
    static_trait_fields: Counter[str] = Counter()

    for path in candidates[:20]:
        payload = load_json(path)

        if payload is None:
            continue

        fields: Counter[str] = Counter()

        walk_json(
            payload,
            fields=fields,
        )

        for field_name, count in fields.items():
            if "trait" in field_name.lower():
                riot_trait_fields[field_name] += count

    for path in static_files[:40]:
        payload = load_json(path)

        if payload is None:
            continue

        fields: Counter[str] = Counter()

        walk_json(
            payload,
            fields=fields,
        )

        for field_name, count in fields.items():
            if "trait" in field_name.lower():
                static_trait_fields[field_name] += count

    R.write("RIOT MATCH:")
    for field_name, count in riot_trait_fields.most_common(60):
        R.write(
            f"  {field_name:<80} {count}"
        )

    R.write()
    R.write("STATIC DATA:")

    for field_name, count in static_trait_fields.most_common(60):
        R.write(
            f"  {field_name:<80} {count}"
        )


# ======================================================================================
# 16. Individual unit damage
# ======================================================================================


def audit_unit_damage(candidates: list[Path]) -> None:
    R.section("16. EXISTE DANO INDIVIDUAL POR UNIDADE?")

    damage_patterns = re.compile(
        r"(damage|dmg|damage_dealt|damageDealt|"
        r"physicalDamage|magicDamage|trueDamage)",
        re.IGNORECASE,
    )

    found: list[str] = []

    for path in candidates[:30]:
        payload = load_json(path)

        if payload is None:
            continue

        units = find_first_participant_units(payload)

        if not units:
            continue

        for unit in units:
            if not isinstance(unit, dict):
                continue

            for key, value in unit.items():
                if damage_patterns.search(str(key)):
                    found.append(
                        f"{relative(path)} -> "
                        f"{key} = {repr(value)}"
                    )

    if not found:
        R.write(
            "Nenhum campo de dano individual por unidade foi encontrado "
            "nos participant.units analisados."
        )
    else:
        for item in found[:100]:
            R.write(item)


# ======================================================================================
# 17. Position / frontline / backline
# ======================================================================================


def audit_position_data(
    candidates: list[Path],
    static_files: list[Path],
) -> None:
    R.section("17. POSIÇÃO / FRONTLINE / BACKLINE")

    keywords = re.compile(
        r"(position|row|column|cell|hex|"
        r"frontline|backline|range)",
        re.IGNORECASE,
    )

    found: Counter[str] = Counter()

    for path in candidates[:20] + static_files[:40]:
        payload = load_json(path)

        if payload is None:
            continue

        fields: Counter[str] = Counter()

        walk_json(
            payload,
            fields=fields,
        )

        for field_name, count in fields.items():
            if keywords.search(field_name):
                found[field_name] += count

    if not found:
        R.write(
            "Nenhum sinal estrutural de posição encontrado."
        )
        return

    for field_name, count in found.most_common(100):
        R.write(
            f"{field_name:<90} {count}"
        )


# ======================================================================================
# 18. Possível circularidade de aprendizado
# ======================================================================================


def audit_learning_cycle() -> None:
    R.section("18. FLUXO DE BOOTSTRAP / POSSÍVEL CIRCULARIDADE")

    targets = [
        ROOT / "src/role_inference/services/unit_role_seed_inference.py",
        ROOT / "src/role_inference/services/item_observation_collector.py",
        ROOT / "src/role_inference/services/statistical_item_classifier.py",
        ROOT / "src/role_inference/services/hybrid_item_classifier.py",
        ROOT / "src/role_inference/services/item_learning_cycle.py",
        ROOT / "scripts/run_challenger_item_benchmark.py",
    ]

    regex = re.compile(
        r"(UnitRoleSeed|seed|observation|collect|"
        r"StatisticalItemClassifier|HybridItemClassifier|"
        r"MetadataItemClassifier|classif|benchmark)",
        re.IGNORECASE,
    )

    for path in targets:
        if not path.exists():
            continue

        text = read_text(path) or ""

        hits: list[tuple[int, str]] = []

        for number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if regex.search(line):
                hits.append(
                    (number, clean(line))
                )

        if not hits:
            continue

        R.subsection(relative(path))

        for number, line in hits[:150]:
            R.write(
                f"{number:5d}: {line}"
            )


# ======================================================================================
# 19. Sinais possíveis para V2
# ======================================================================================


def audit_candidate_signal_matrix(
    riot_candidates: list[Path],
    static_files: list[Path],
) -> None:
    R.section("19. MATRIZ DE SINAIS CANDIDATOS PARA V2")

    # Detecta apenas presença estrutural, sem sugerir peso.
    all_text = ""

    for path in riot_candidates[:10] + static_files[:20]:
        text = read_text(path)

        if text:
            all_text += "\n" + text[:2_000_000]

    lower = all_text.lower()

    signals = [
        (
            "itemização final",
            True,
            "UnitSnapshot.items já confirmado",
        ),
        (
            "tier / estrelas",
            True,
            "UnitSnapshot.tier já confirmado",
        ),
        (
            "rarity / custo aproximado",
            True,
            "UnitSnapshot.rarity já confirmado",
        ),
        (
            "traits da composição",
            '"traits"' in lower or "trait" in lower,
            "buscar integração por unit/composição",
        ),
        (
            "attack range",
            "attackrange" in lower
            or "attack_range" in lower,
            "static data",
        ),
        (
            "health",
            '"health"' in lower
            or ".health" in lower,
            "static data",
        ),
        (
            "armor",
            '"armor"' in lower,
            "static data",
        ),
        (
            "magic resist",
            "magicresist" in lower
            or "magic_resist" in lower,
            "static data",
        ),
        (
            "attack damage",
            "attackdamage" in lower
            or "attack_damage" in lower,
            "static data",
        ),
        (
            "attack speed",
            "attackspeed" in lower
            or "attack_speed" in lower,
            "static data",
        ),
        (
            "mana",
            '"mana"' in lower,
            "static data",
        ),
        (
            "role explícito",
            '"role"' in lower
            or '"roles"' in lower,
            "static data",
        ),
        (
            "archetype explícito",
            '"archetype"' in lower,
            "static data",
        ),
        (
            "posição real board",
            '"position"' in lower
            or '"row"' in lower
            or '"column"' in lower,
            "Riot/static",
        ),
        (
            "dano individual da unidade",
            False,
            "será validado separadamente na seção 16",
        ),
        (
            "perfil estatístico de item",
            True,
            "StatisticalItemClassifier existente",
        ),
        (
            "metadata textual de item",
            True,
            "MetadataItemClassifier existente",
        ),
    ]

    R.write(
        f"{'SINAL':<38} {'DISPONÍVEL?':<14} OBSERVAÇÃO"
    )
    R.write("-" * 100)

    for name, available, note in signals:
        R.write(
            f"{name:<38} "
            f"{'SIM' if available else 'NÃO/VERIFICAR':<14} "
            f"{note}"
        )


# ======================================================================================
# 20. Consumer limitations
# ======================================================================================


def audit_unit_snapshot_gap() -> None:
    R.section("20. GAP ENTRE DADOS DISPONÍVEIS E UNIT SNAPSHOT")

    unit_path = (
        ROOT
        / "src/performance_engine/models/unit_snapshot.py"
    )

    text = read_text(unit_path) or ""

    current_fields = []

    tree = parse_python(unit_path)

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    current_fields.append(node.target.id)

    R.write("Campos atuais de UnitSnapshot:")

    for field_name in current_fields:
        R.write(
            f"  - {field_name}"
        )

    R.write()
    R.write(
        "A auditoria das seções anteriores deve mostrar se o static data "
        "possui sinais adicionais que poderiam ser resolvidos externamente "
        "sem necessariamente alterar o Riot contract."
    )


# ======================================================================================
# 21. Questions
# ======================================================================================


def audit_questions() -> None:
    R.section("21. CHECKLIST PARA FECHAR O ALGORITMO V2")

    questions = [
        "[A] Riot Match fornece dano individual por unidade?",
        "[B] Riot Match fornece posição/hex/row da unidade final?",
        "[C] Riot Match fornece apenas character_id/tier/rarity/items?",
        "[D] Static data fornece custo real da unidade?",
        "[E] Static data fornece attack range?",
        "[F] Static data fornece HP?",
        "[G] Static data fornece armor?",
        "[H] Static data fornece MR?",
        "[I] Static data fornece AD?",
        "[J] Static data fornece attack speed?",
        "[K] Static data fornece mana?",
        "[L] Static data fornece role/archetype oficial?",
        "[M] Static data fornece traits por unidade?",
        "[N] Há descrição da habilidade utilizável como sinal?",
        "[O] UnitRoleSeedInference usa posição?",
        "[P] UnitRoleSeedInference usa apenas itens?",
        "[Q] O seed pode gerar circularidade no aprendizado dos itens?",
        "[R] MetadataItemClassifier reduz essa circularidade?",
        "[S] HybridItemClassifier dá mais peso ao benchmark quando há amostra?",
        "[T] Existem sinais que o projeto possui mas UnitSnapshot descarta?",
        "[U] Podemos inferir frontline/backline sem hardcode de campeão?",
        "[V] Podemos construir perfil ofensivo/defensivo por stats estáticos?",
        "[W] Podemos penalizar carry quando defense >> offense?",
        "[X] Podemos identificar secondary carry sem forçar classificação?",
        "[Y] Podemos retornar primary_carry=None com confiança baixa?",
        "[Z] Quais sinais devem ser evidência e quais devem ser tie-break?",
    ]

    for question in questions:
        R.write(f"  {question}")


# ======================================================================================
# 22. Resumo
# ======================================================================================


def audit_summary() -> None:
    R.section("22. RESUMO")

    R.write(
        "Objetivo desta auditoria:"
    )
    R.write()
    R.write(
        "  descobrir quais sinais existem de verdade antes de "
        "definir a fórmula do Unit Role Intelligence V2."
    )

    R.write()
    R.write(
        "Nenhuma decisão de peso deve ser implementada apenas "
        "com base neste script."
    )

    R.write()
    R.write(
        "Nenhum arquivo do produto foi modificado."
    )


# ======================================================================================
# Main
# ======================================================================================


def main() -> int:
    audit_files()
    audit_role_sources()
    audit_models()

    audit_seed_inference()
    audit_metadata_classifier_rules()
    audit_hybrid_classifier()

    riot_candidates = audit_riot_json_files()

    audit_riot_schema(riot_candidates)
    audit_real_units(riot_candidates)

    static_files = audit_static_files()

    audit_static_schema(static_files)
    audit_unit_metadata_examples(static_files)
    audit_explicit_roles(static_files)
    audit_stats(static_files)

    audit_traits(
        riot_candidates,
        static_files,
    )

    audit_unit_damage(riot_candidates)

    audit_position_data(
        riot_candidates,
        static_files,
    )

    audit_learning_cycle()

    audit_candidate_signal_matrix(
        riot_candidates,
        static_files,
    )

    audit_unit_snapshot_gap()
    audit_questions()
    audit_summary()

    R.save(OUTPUT_FILE)

    print("=" * 90)
    print("TFT INSIGHT — ROLE V2 DATA SOURCES AUDIT")
    print("=" * 90)
    print()
    print("Auditoria concluída.")
    print("Modo: SOMENTE LEITURA")
    print()
    print("Relatório gerado:")
    print(OUTPUT_FILE)
    print()
    print("Envie o TXT no ChatGPT para análise.")
    print("=" * 90)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())