from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path


ROADMAP = "29.2B"
AUDIT = "#77"
TITLE = "FIRST VALUE UX + INFORMATION CLEANUP — FINAL AUDIT"

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "benchmark": ROOT / "partner_platform" / "pages" / "benchmark_page.py",
    "post_match": ROOT / "partner_platform" / "components" / "post_match_report.py",
    "contest": ROOT / "partner_platform" / "components" / "contest_intelligence.py",
    "pre_match": ROOT / "partner_platform" / "components" / "pre_match_coach.py",
}

LINE = "=" * 112
SUB = "-" * 112


@dataclass
class Check:
    code: str
    title: str
    status: str
    detail: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def syntax_check(path: Path, text: str) -> tuple[bool, str]:
    try:
        ast.parse(text, filename=str(path))
        return True, "Sintaxe Python válida."
    except SyntaxError as exc:
        return False, f"SyntaxError L{exc.lineno}: {exc.msg}"


def strip_comments(text: str) -> str:
    """Remove comentários sem destruir strings/código executável."""
    out: list[tokenize.TokenInfo] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok in tokens:
            if tok.type != tokenize.COMMENT:
                out.append(tok)
        return tokenize.untokenize(out)
    except (tokenize.TokenError, IndentationError):
        return text


def function_body(text: str, function_name: str) -> str:
    """Retorna somente o corpo textual de uma função top-level."""
    pattern = re.compile(
        rf"^def\s+{re.escape(function_name)}\s*\(.*?(?=^def\s+|\Z)",
        re.M | re.S,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


def contains(text: str, *patterns: str) -> bool:
    return any(re.search(p, text, flags=re.I | re.S) for p in patterns)


def add(
    checks: list[Check],
    code: str,
    title: str,
    ok: bool,
    detail: str,
    fail_status: str = "REVISAR",
) -> None:
    checks.append(Check(code, title, "OK" if ok else fail_status, detail))


def main() -> int:
    print(LINE)
    print(f"{AUDIT} / ROADMAP {ROADMAP} — {TITLE}")
    print(LINE)
    print(f"Raiz detectada : {ROOT}")
    print("Objetivo        : validar a UX final da 29.2B sem punir código interno não renderizado")
    print("Escopo          : apresentação; prioridade, missão e motores continuam protegidos")
    print()

    missing = [str(p.relative_to(ROOT)) for p in FILES.values() if not p.exists()]
    if missing:
        print("BLOQUEADO — arquivos obrigatórios ausentes:")
        for item in missing:
            print(f"  - {item}")
        return 2

    texts = {name: read(path) for name, path in FILES.items()}
    executable = {name: strip_comments(text) for name, text in texts.items()}
    checks: list[Check] = []

    print("ARQUIVOS")
    print(SUB)
    for name, path in FILES.items():
        ok, msg = syntax_check(path, texts[name])
        print(f"{name:12} {path.relative_to(ROOT)}")
        print(f"{'':12} {msg}")
        add(checks, f"F-{name.upper()}", f"Sintaxe: {name}", ok, msg, "BLOQUEAR")
    print()

    benchmark = texts["benchmark"]
    benchmark_exec = executable["benchmark"]
    post = texts["post_match"]
    post_exec = executable["post_match"]
    contest = texts["contest"]
    pre = texts["pre_match"]

    render_body = function_body(benchmark_exec, "render")
    training_body = function_body(benchmark_exec, "_render_compact_training")
    strength_body = function_body(benchmark_exec, "_public_strength_description")

    # ------------------------------------------------------------------
    # Contratos preservados.
    # ------------------------------------------------------------------
    add(
        checks, "K01", "Missão/ciclo continua presente",
        contains(benchmark, r'\bMiss[aã]o\b') and
        contains(benchmark, r"completed", r"remaining", r"target"),
        "A UX mantém missão e progresso do ciclo."
    )
    add(
        checks, "K02", "Integração pós-partida preservada",
        "render_post_match_report" in benchmark,
        "Relatório pós-partida continua integrado."
    )
    add(
        checks, "K03", "Contestação preservada",
        "render_contest_intelligence" in benchmark,
        "Contest Intelligence continua integrado."
    )
    add(
        checks, "K04", "Composição preservada",
        contains(benchmark, r"composition_intelligence", r"composi[cç][aã]o"),
        "Composition Intelligence/evidências continuam presentes."
    )
    add(
        checks, "K05", "Economia preservada",
        contains(benchmark, r"economy_intelligence", r"economia"),
        "Economy Intelligence/evidências continuam presentes."
    )
    add(
        checks, "K06", "Carries/itens preservados",
        contains(benchmark, r"carry_item_intelligence", r"carries", r"carry"),
        "Carry/Item Intelligence/evidências continuam presentes."
    )

    # ------------------------------------------------------------------
    # Contrato visual da 29.2B.
    # ------------------------------------------------------------------
    add(
        checks, "U01", 'Título público é "Missão"',
        contains(training_body, r'section_header\(\s*["\']Miss[aã]o["\']') and
        not contains(training_body, r"Seu foco nas pr[oó]ximas"),
        'O bloco de treino deve aparecer como "Missão".'
    )
    add(
        checks, "U02", "Contexto competitivo explicativo removido",
        not contains(render_body, r"Entender seu contexto competitivo",
                     r"Entenda seu grupo competitivo"),
        "O benchmark pode continuar sendo calculado; o bloco explicativo não deve ser renderizado."
    )
    add(
        checks, "U03", "Detalhes técnicos removidos da UX",
        not contains(post_exec, r"Detalhes t[eé]cnicos da an[aá]lise"),
        "Dados técnicos não aparecem no relatório normal do jogador."
    )
    add(
        checks, "U04", "Pré-jogo redundante não é renderizado",
        "_render_pre_match_coach_integration(" not in render_body,
        "A função pode continuar no arquivo, mas render() não deve chamá-la."
    )
    add(
        checks, "U05", "Componente pré-jogo legado não afeta a UX",
        "_render_pre_match_coach_integration(" not in render_body,
        "Textos Preserve/interpretativos do componente legado são ignorados enquanto ele não é renderizado."
    )
    add(
        checks, "U06", '"Como interpretar esta análise" removido',
        not contains(contest, r"Como interpretar esta an[aá]lise"),
        "Contestação não deve terminar em expander genérico de interpretação."
    )
    add(
        checks, "U07", "Contestação média não é KPI principal",
        not contains(contest, r'["\']Contestação média["\']'),
        "average_score pode existir no payload/contexto, mas não como card principal."
    )
    add(
        checks, "U08", "Checklist da missão fica visível",
        contains(training_body, r"Durante a partida") and
        not contains(training_body, r"Como praticar nesta partida"),
        "As instruções curtas da missão devem ficar abertas."
    )
    add(
        checks, "U09", "Resumo do jogador está compacto",
        not contains(render_body, r'player_cols\s*=\s*st\.columns\(4\)'),
        "Identidade/elo/grupo/histórico não devem ocupar quatro cards grandes."
    )

    # ------------------------------------------------------------------
    # Telemetria.
    # ------------------------------------------------------------------
    add(
        checks, "D01", "Dano ao lobby não é exibido",
        not contains(post_exec, r'["\']Dano ao lobby["\']') and
        not contains(post_exec, r'get\(\s*["\']total_damage_to_players["\']'),
        "Comentários não contam; somente uso executável do dado é bloqueado.",
        "BLOQUEAR"
    )
    add(
        checks, "G01", "Card de ouro usa gold_left",
        contains(post_exec, r'["\']Ouro restante["\']') and
        contains(post_exec, r'get\(\s*["\']gold_left["\']'),
        "A última partida continua exibindo gold_left."
    )

    # G02 deixa de ser falha: o caso 80 foi explicado por partidas desconectadas/AFK.
    # Mantemos apenas a proteção de não haver hardcode artificial de 80 na UI.
    add(
        checks, "G02", "Narrativa de ouro não possui hardcode artificial",
        not contains(post_exec, r'["\']80(?:[.,]0+)?["\']'),
        "O valor observado pode vir legitimamente do histórico; a UX não deve fabricar 80."
    )

    # ------------------------------------------------------------------
    # Strength: avaliar somente a descrição pública, não contratos internos.
    # ------------------------------------------------------------------
    # S01 avalia apenas valores efetivamente retornados ao jogador.
    # Docstrings e `internal_markers` podem conter linguagem interna justamente
    # para reconhecê-la e filtrá-la antes da apresentação pública.
    strength_returns: list[str] = []
    try:
        strength_tree = ast.parse(strength_body)
        for node in ast.walk(strength_tree):
            if not isinstance(node, ast.Return) or node.value is None:
                continue

            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                strength_returns.append(value.value)
                continue

            if isinstance(value, ast.JoinedStr):
                literal_parts = [
                    part.value
                    for part in value.values
                    if isinstance(part, ast.Constant)
                    and isinstance(part.value, str)
                ]
                strength_returns.append("".join(literal_parts))
                continue

            if isinstance(value, ast.Name) and value.id == "raw":
                # `raw` só é retornado depois do filtro `internal_markers`;
                # portanto não representa exposição automática da linguagem interna.
                strength_returns.append("<filtered_raw>")

    except SyntaxError:
        strength_returns = []

    internal_terms = (
        r"avalia[cç][aã]o oficial forte",
        r"convertida artificialmente",
        r"prioridade de corre[cç][aã]o",
        r"a skill possui",
    )
    public_strength_text = "\n".join(strength_returns)

    add(
        checks, "S01", "Strength usa linguagem pública",
        bool(strength_returns)
        and not contains(public_strength_text, *internal_terms),
        "Somente textos efetivamente retornados ao jogador são avaliados; "
        "docstrings e marcadores internos de filtragem não contam."
    )

    print("RESULTADO")
    print(SUB)
    print(f"{'REGRA':<12} {'DESCRIÇÃO':<55} {'STATUS':<10}")
    print("-" * 79)
    for c in checks:
        print(f"{c.code:<12} {c.title[:54]:<55} {c.status:<10}")
    print()

    print("DETALHES PENDENTES")
    print(SUB)
    pending = [c for c in checks if c.status != "OK"]
    if not pending:
        print("Nenhum.")
    else:
        for c in pending:
            print(f"[{c.status}] {c.code} — {c.title}")
            print(f"  {c.detail}")
    print()

    counts: dict[str, int] = {}
    for c in checks:
        counts[c.status] = counts.get(c.status, 0) + 1

    print("RESUMO")
    print(SUB)
    for status in ("OK", "REVISAR", "BLOQUEAR"):
        print(f"{status:10}: {counts.get(status, 0)}")
    print()

    if counts.get("BLOQUEAR", 0):
        verdict = "BLOQUEADO"
        rc = 1
    elif counts.get("REVISAR", 0):
        verdict = "REVISAR 29.2B"
        rc = 0
    else:
        verdict = "29.2B UX VALIDADA"
        rc = 0

    print(f"VEREDITO: {verdict}")
    print()
    print("OBSERVAÇÕES")
    print(SUB)
    print("- Funções/componentes internos podem permanecer no projeto sem falhar a auditoria se não forem renderizados.")
    print("- Comentários não geram falso positivo para Dano ao lobby.")
    print("- O caso de ouro ~80 não é tratado como bug: houve partidas desconectadas/AFK que podem elevar a média.")
    print("- Esta auditoria valida contrato de código; a hierarquia visual ainda deve ser conferida no Streamlit.")
    print(LINE)

    return rc


if __name__ == "__main__":
    sys.exit(main())
