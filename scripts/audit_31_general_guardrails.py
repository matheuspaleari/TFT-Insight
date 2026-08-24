from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

SOURCE_ROOTS = (
    ROOT / "src",
    ROOT / "partner_platform",
)

# Aqui procuramos somente afirmações POSITIVAS/determinísticas.
# Frases protetivas como "não prova que X causou Y" NÃO devem casar.
FORBIDDEN_PUBLIC_PATTERNS = (
    r"(?<!não )(?<!nao )\bvocê errou porque\b",
    r"(?<!não )(?<!nao )\bvoce errou porque\b",
    r"(?<!não )(?<!nao )\bdeveria ter rolado\b",
    r"(?<!não )(?<!nao )\bdeveria ter comprado xp\b",
    r"(?<!não )(?<!nao )\bdeveria ter subido de nível\b",
    r"(?<!não )(?<!nao )\bdeveria ter subido de nivel\b",
    r"(?<!não )(?<!nao )\ba contestação causou\b",
    r"(?<!não )(?<!nao )\ba contestacao causou\b",
    r"(?<!não )(?<!nao )\bcausou sua derrota\b",
    r"(?<!não )(?<!nao )\bcausou a derrota\b",
    r"(?<!não )(?<!nao )\bessa build causou\b",
    r"(?<!não )(?<!nao )\besses itens causaram\b",
    r"(?<!não )(?<!nao )\bpivotar era obrigatório\b",
    r"(?<!não )(?<!nao )\bpivotar era obrigatorio\b",
    r"(?<!não )(?<!nao )\bfast 9 é sempre melhor\b",
    r"(?<!não )(?<!nao )\bfast 9 e sempre melhor\b",
    r"(?<!não )(?<!nao )\bessa composição é a melhor\b",
    r"(?<!não )(?<!nao )\bessa composicao e a melhor\b",
    r"(?<!não )(?<!nao )\bvocê não fez scout\b",
    r"(?<!não )(?<!nao )\bvoce nao fez scout\b",
)

# Frases de negação/guardrail conhecidas.
NEGATION_GUARDRAIL_MARKERS = (
    "não prova que",
    "nao prova que",
    "não significa que",
    "nao significa que",
    "não é causa",
    "nao e causa",
    "associação",
    "associacao",
    "não deve",
    "nao deve",
    "não sabe",
    "nao sabe",
    "não revela",
    "nao revela",
    "não informa",
    "nao informa",
)

REQUIRED_CONCEPTS = {
    "causality": (
        "não prova causalidade",
        "não prova que",
        "associação histórica",
        "associação, não",
        "não significa que",
    ),
    "board_final": (
        "board final",
        "estado final",
        "final observado",
    ),
    "timing_unknown": (
        "timing",
        "não informa",
        "não revela",
    ),
    "scout_unknown": (
        "não sabe se o jogador fez scout",
        "não prova que você fez scout",
    ),
    "sample_size": (
        "amostra mínima",
        "amostra insuficiente",
        "exploratória",
        "eligible_for_comparison",
        "min_sample",
        "min_group_sample",
    ),
    "mission_protection": (
        "não altera sua missão",
        "não troca sua missão",
        "changes_mission",
    ),
    "priority_protection": (
        "não altera sua prioridade",
        "não cria uma nova prioridade",
        "changes_learning_priority",
    ),
}

CRITICAL_FILES = (
    "partner_platform/components/pre_match_coach.py",
    "src/composition_intelligence_v2/services/composition_intelligence_v2.py",
    "src/contest_intelligence/services/contest_player_presenter.py",
    "src/economy_intelligence/services/economy_player_presenter.py",
    "src/carry_item_intelligence/services/carry_item_player_presenter.py",
)

PROTECTED_FLAGS = (
    "changes_learning_priority",
    "changes_mission",
    "changes_difficulty",
    "changes_evidence_class",
    "counts_as_mission_evidence",
    "predicts_rank_up",
)

# G06 passa a ser auditado por módulo, e não arquivo-a-arquivo.
# Models/__init__/helpers não precisam repetir texto público de amostra.
SAMPLE_MODULES = {
    "composition": (
        "src/composition_intelligence_v2",
        "partner_platform/components/composition",
    ),
    "contest": (
        "src/contest_intelligence",
        "partner_platform/components/contest",
    ),
    "economy": (
        "src/economy_intelligence",
        "partner_platform/components/economy",
    ),
    "carry_item": (
        "src/carry_item_intelligence",
        "partner_platform/components/carry_item",
    ),
    "post_match": (
        "src/post_match",
        "partner_platform/components/post_match",
    ),
    "pre_match": (
        "partner_platform/components/pre_match_coach.py",
    ),
}

SAMPLE_GUARDRAIL_MARKERS = (
    "amostra mínima",
    "amostra minima",
    "amostra insuficiente",
    "exploratória",
    "exploratoria",
    "eligible_for_comparison",
    "min_sample",
    "min_group_sample",
    "statistical_confidence",
    "confidence",
)


@dataclass
class Finding:
    severity: str
    rule_id: str
    file: str
    line: int
    message: str
    excerpt: str = ""


@dataclass
class RuleSummary:
    rule_id: str
    passed: bool
    findings: int
    description: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="#31 / Roadmap 20 — Auditoria geral dos Guardrails."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falha também em warnings.",
    )
    return parser.parse_args()


def iter_python_files() -> Iterable[Path]:
    for source_root in SOURCE_ROOTS:
        if not source_root.exists():
            continue
        for path in source_root.rglob("*.py"):
            if "__pycache__" not in path.parts:
                yield path


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def add_finding(
    findings: list[Finding],
    *,
    severity: str,
    rule_id: str,
    path: Path,
    line: int,
    message: str,
    excerpt: str = "",
) -> None:
    findings.append(
        Finding(
            severity=severity,
            rule_id=rule_id,
            file=relative(path),
            line=line,
            message=message,
            excerpt=excerpt.strip(),
        )
    )


def audit_syntax(files, findings):
    before = len(findings)
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except Exception as error:
            add_finding(
                findings,
                severity="BLOCKER",
                rule_id="G01_SYNTAX",
                path=path,
                line=getattr(error, "lineno", 0) or 0,
                message=f"Arquivo Python inválido: {error}",
            )
    found = len(findings) - before
    return RuleSummary(
        "G01_SYNTAX",
        found == 0,
        found,
        "Todo código Python auditado deve ser parseável.",
    )


def _line_is_guardrail(line: str) -> bool:
    lowered = line.lower()
    return any(
        marker in lowered
        for marker in NEGATION_GUARDRAIL_MARKERS
    )


def audit_forbidden_public_claims(files, findings):
    before = len(findings)

    compiled = [
        re.compile(pattern, flags=re.IGNORECASE)
        for pattern in FORBIDDEN_PUBLIC_PATTERNS
    ]

    # Não precisamos vasculhar testes/auditores que citam frases proibidas
    # deliberadamente.
    ignore_tokens = (
        "scripts",
        "tests",
        "test_",
        "validate_",
        "diagnose_",
        "diagnostics",
    )

    for path in files:
        rel = relative(path).replace("\\", "/").lower()

        if any(token in rel for token in ignore_tokens):
            continue

        # G02 foca em superfícies que podem gerar texto público.
        is_public_surface = (
            "partner_platform/" in rel
            or "presenter" in path.name.lower()
            or "interpretation" in path.name.lower()
            or "recommendation" in path.name.lower()
            or "coach" in path.name.lower()
        )

        if not is_public_surface:
            continue

        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            1,
        ):
            if _line_is_guardrail(line):
                # Ex.: "não prova que a contestação causou o resultado."
                # Isso é exatamente o que queremos preservar.
                continue

            if any(regex.search(line) for regex in compiled):
                add_finding(
                    findings,
                    severity="BLOCKER",
                    rule_id="G02_FORBIDDEN_CLAIM",
                    path=path,
                    line=line_number,
                    message=(
                        "Afirmação pública proibida/determinística detectada."
                    ),
                    excerpt=line,
                )

    found = len(findings) - before
    return RuleSummary(
        "G02_FORBIDDEN_CLAIM",
        found == 0,
        found,
        (
            "A superfície pública não pode afirmar causalidade, "
            "decisões invisíveis ou obrigação sem telemetria."
        ),
    )


def audit_required_guardrail_concepts(files, findings):
    before = len(findings)
    corpus = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in files
    )

    for concept, variants in REQUIRED_CONCEPTS.items():
        if not any(v.lower() in corpus for v in variants):
            add_finding(
                findings,
                severity="BLOCKER",
                rule_id="G03_REQUIRED_CONCEPT",
                path=ROOT,
                line=0,
                message=f"Guardrail conceitual ausente: {concept}",
                excerpt=" | ".join(variants),
            )

    found = len(findings) - before
    return RuleSummary(
        "G03_REQUIRED_CONCEPT",
        found == 0,
        found,
        "Conceitos mínimos de segurança analítica precisam existir.",
    )


def audit_critical_files(findings):
    before = len(findings)

    for item in CRITICAL_FILES:
        path = ROOT / item
        if not path.exists():
            add_finding(
                findings,
                severity="BLOCKER",
                rule_id="G04_CRITICAL_FILE",
                path=path,
                line=0,
                message="Arquivo crítico de guardrail não encontrado.",
            )

    found = len(findings) - before
    return RuleSummary(
        "G04_CRITICAL_FILE",
        found == 0,
        found,
        "Módulos críticos da camada pública precisam existir.",
    )


def audit_protected_flags(files, findings):
    before = len(findings)

    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue

            for target in targets:
                name = None

                if isinstance(target, ast.Name):
                    name = target.id
                elif isinstance(target, ast.Attribute):
                    name = target.attr

                if name not in PROTECTED_FLAGS:
                    continue

                literal_value = None
                if isinstance(value, ast.Constant):
                    literal_value = value.value

                if literal_value is True:
                    add_finding(
                        findings,
                        severity="BLOCKER",
                        rule_id="G05_PROTECTED_FLAG",
                        path=path,
                        line=getattr(node, "lineno", 0),
                        message=(
                            f"Flag protegida atribuída diretamente como True: {name}"
                        ),
                    )

    found = len(findings) - before
    return RuleSummary(
        "G05_PROTECTED_FLAG",
        found == 0,
        found,
        (
            "Camadas analíticas não devem promover silenciosamente missão, "
            "prioridade, evidência ou previsão de rank."
        ),
    )


def audit_sample_language(files, findings):
    before = len(findings)

    normalized_files = [
        (
            path,
            relative(path).replace("\\", "/").lower(),
            path.read_text(encoding="utf-8").lower(),
        )
        for path in files
    ]

    for module_name, tokens in SAMPLE_MODULES.items():
        module_texts = [
            text
            for _, rel, text in normalized_files
            if any(token.lower() in rel for token in tokens)
        ]

        if not module_texts:
            # pre_match pode não ter lógica própria de sample; ele apenas
            # consolida módulos. Ausência do arquivo já é tratada em G04.
            if module_name == "pre_match":
                continue

            add_finding(
                findings,
                severity="WARNING",
                rule_id="G06_SAMPLE_LANGUAGE",
                path=ROOT,
                line=0,
                message=f"Módulo não localizado para auditoria de amostra: {module_name}",
            )
            continue

        corpus = "\n".join(module_texts)

        # Só exige marker se o módulo contém comparação/estatística histórica.
        comparison_present = any(
            token in corpus
            for token in (
                "average_placement",
                "top4_rate",
                "win_rate",
                "comparison",
                "best_supported",
                "eligible_for_comparison",
                "statistical_confidence",
            )
        )

        if not comparison_present:
            continue

        has_guardrail = any(
            marker in corpus
            for marker in SAMPLE_GUARDRAIL_MARKERS
        )

        if not has_guardrail:
            add_finding(
                findings,
                severity="WARNING",
                rule_id="G06_SAMPLE_LANGUAGE",
                path=ROOT,
                line=0,
                message=(
                    f"Módulo {module_name} faz comparação histórica "
                    "sem marker de amostra/confiança."
                ),
            )

    found = len(findings) - before
    return RuleSummary(
        "G06_SAMPLE_LANGUAGE",
        found == 0,
        found,
        (
            "Amostra/confiança é validada no nível do módulo, sem exigir "
            "que __init__, models e helpers repitam texto público."
        ),
    )


def audit_direct_rank_language(files, findings):
    before = len(findings)

    suspicious = (
        "vai subir de elo",
        "vai subir de rank",
        "garante promoção",
        "garante promocao",
        "você vai chegar ao challenger",
        "voce vai chegar ao challenger",
    )

    for path in files:
        rel = relative(path).replace("\\", "/").lower()

        if any(
            token in rel
            for token in (
                "scripts",
                "tests",
                "test_",
                "validate_",
            )
        ):
            continue

        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            1,
        ):
            if any(
                phrase in line.lower()
                for phrase in suspicious
            ):
                add_finding(
                    findings,
                    severity="BLOCKER",
                    rule_id="G07_RANK_PREDICTION",
                    path=path,
                    line=line_number,
                    message="Previsão/promessa direta de rank detectada.",
                    excerpt=line,
                )

    found = len(findings) - before
    return RuleSummary(
        "G07_RANK_PREDICTION",
        found == 0,
        found,
        "O Coach não promete rank-up nem promoção.",
    )


def audit_public_internal_labels(files, findings):
    before = len(findings)

    public_files = [
        path
        for path in files
        if (
            "partner_platform/components"
            in relative(path).replace("\\", "/")
            or "presenter" in path.name.lower()
        )
    ]

    tokens = (
        "EvidenceClass.",
        '"PROXY"',
        '"CONTEXT"',
        '"DIRECT"',
    )

    for path in public_files:
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            1,
        ):
            if any(token in line for token in tokens):
                add_finding(
                    findings,
                    severity="WARNING",
                    rule_id="G08_INTERNAL_LABEL",
                    path=path,
                    line=line_number,
                    message="Possível label interna exposta na camada pública.",
                    excerpt=line,
                )

    found = len(findings) - before
    return RuleSummary(
        "G08_INTERNAL_LABEL",
        found == 0,
        found,
        "Labels internas de evidência não devem vazar para a UI.",
    )


def main() -> None:
    args = parse_args()
    files = list(iter_python_files())
    findings: list[Finding] = []

    summaries = [
        audit_syntax(files, findings),
        audit_forbidden_public_claims(files, findings),
        audit_required_guardrail_concepts(files, findings),
        audit_critical_files(findings),
        audit_protected_flags(files, findings),
        audit_sample_language(files, findings),
        audit_direct_rank_language(files, findings),
        audit_public_internal_labels(files, findings),
    ]

    blockers = [
        f
        for f in findings
        if f.severity == "BLOCKER"
    ]
    warnings = [
        f
        for f in findings
        if f.severity == "WARNING"
    ]

    output_dir = ROOT / "data/diagnostics/guardrail_audit"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = output_dir / f"guardrail_audit_{timestamp}.json"

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strict": args.strict,
        "files_scanned": len(files),
        "rules": [asdict(item) for item in summaries],
        "findings": [asdict(item) for item in findings],
        "summary": {
            "blockers": len(blockers),
            "warnings": len(warnings),
            "rules_passed": sum(item.passed for item in summaries),
            "rules_total": len(summaries),
        },
    }

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 110)
    print("#31 / ROADMAP 20 - AUDITORIA GERAL DOS GUARDRAILS")
    print("=" * 110)
    print(f"Arquivos auditados : {len(files)}")
    print(f"Modo strict        : {args.strict}")

    print()
    print("REGRAS")
    print("-" * 110)

    for item in summaries:
        print(
            f"{item.rule_id:<24} "
            f"{'OK' if item.passed else 'REVISAR':<8} "
            f"findings={item.findings}"
        )

    if findings:
        print()
        print("FINDINGS")
        print("-" * 110)

        for finding in findings:
            print(
                f"[{finding.severity}] {finding.rule_id} | "
                f"{finding.file}:{finding.line}"
            )
            print(f"  {finding.message}")
            if finding.excerpt:
                print(f"  > {finding.excerpt[:220]}")

    print()
    print("RESUMO")
    print("-" * 110)
    print(f"Blockers       : {len(blockers)}")
    print(f"Warnings       : {len(warnings)}")
    print(
        f"Regras OK      : "
        f"{sum(item.passed for item in summaries)}/{len(summaries)}"
    )
    print(f"Relatório      : {report_path}")

    should_fail = (
        bool(blockers)
        or (
            args.strict
            and bool(warnings)
        )
    )

    print()
    print("=" * 110)

    if should_fail:
        print("#31 / ROADMAP 20 AUDITORIA DE GUARDRAILS: REVISAR")
        raise SystemExit(1)

    print("#31 / ROADMAP 20 AUDITORIA DE GUARDRAILS: VALIDADA")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
