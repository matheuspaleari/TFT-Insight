from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = (
    ROOT
    / "partner_platform"
    / "components"
    / "carry_item_intelligence.py"
)


def check(label: str, condition: bool) -> bool:
    status = "OK" if condition else "FALHOU"
    print(f"[{status}] {label}")
    return bool(condition)


def main() -> int:
    print("=" * 92)
    print("VALIDACAO 67 - ROADMAP 25.1: CARRIES + ITENS UX V2")
    print("=" * 92)

    if not check("arquivo carry_item_intelligence.py existe", TARGET.exists()):
        return 1

    text = TARGET.read_text(encoding="utf-8")

    try:
        ast.parse(text)
        syntax_ok = True
    except SyntaxError as error:
        syntax_ok = False
        print(f"Erro de sintaxe: {error}")

    checks = [
        check("sintaxe Python valida", syntax_ok),
        check(
            "render principal preservado",
            "def render_carry_item_intelligence(" in text,
        ),
        check(
            "nomes amigaveis de campeoes preservados",
            "friendly_game_name" in text,
        ),
        check(
            "nomes amigaveis de itens preservados",
            "friendly_item_name" in text,
        ),
        check(
            "texto publico amigavel preservado",
            "friendly_public_text" in text,
        ),
        check(
            "cabecalho interno duplicado removido",
            "section_header(" not in text,
        ),
        check(
            "ultima partida vem antes do padrao recorrente",
            text.find("_render_latest(payload)")
            < text.find('st.markdown("#### Seu padrão de carry")'),
        ),
        check(
            "carry mais usado continua disponivel",
            'payload.get("most_used_carry")' in text,
        ),
        check(
            "melhor carry com amostra continua disponivel",
            'payload.get("best_supported_carry")' in text,
        ),
        check(
            "builds recorrentes continuam disponiveis",
            'profile.get("recurring_builds", [])' in text,
        ),
        check(
            "outros carries continuam recolhiveis",
            'st.expander("Ver outros carries"' in text,
        ),
        check(
            "guardrails e limitacoes continuam recolhiveis",
            '"Como interpretar esta análise"' in text
            and 'payload.get("limitations", [])' in text
            and 'coach.get("guardrails", [])' in text,
        ),
        check(
            "estado sem carry explicito existe",
            "não teve um carry público validado" in text,
        ),
        check(
            "itemizacao ganha bloco proprio",
            'st.markdown("#### Padrão de itemização")' in text,
        ),
        check(
            "quantidade de carries deixou de ser KPI principal",
            '"Carries identificados"' not in text,
        ),
    ]

    print("-" * 92)
    passed = sum(checks)
    total = len(checks)
    print(f"Checks aprovados: {passed}/{total}")

    if passed == total:
        print(
            "RESULTADO: CARRIES + ITENS UX V2 ESTRUTURALMENTE CONSISTENTE"
        )
        return 0

    print("RESULTADO: VALIDACAO 67 COM PENDENCIAS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
