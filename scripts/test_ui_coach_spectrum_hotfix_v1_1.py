from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "partner_platform/pages/benchmark_page.py"
NARRATOR = ROOT / "partner_platform/intelligence/local_coach_narrator.py"


def main() -> None:
    page = PAGE.read_text(encoding="utf-8")
    narrator = NARRATOR.read_text(encoding="utf-8")

    ast.parse(page)
    ast.parse(narrator)

    spectrum_start = page.index(
        "def _render_spectrum_bar("
    )
    spectrum_end = page.index(
        "\ndef _spectrum_profile_rows(",
        spectrum_start,
    )
    spectrum_block = page[
        spectrum_start:spectrum_end
    ]

    coach_start = page.index(
        "def _render_coach_contents("
    )
    coach_end = page.index(
        "\ndef _render_floating_coach(",
        coach_start,
    )
    coach_block = page[
        coach_start:coach_end
    ]

    checks = [
        (
            "Spectrum usa componente nativo",
            "st.progress(" in spectrum_block,
        ),
        (
            "Spectrum não usa HTML bruto",
            "unsafe_allow_html" not in spectrum_block,
        ),
        (
            "Spectrum não contém div manual",
            "<div" not in spectrum_block,
        ),
        (
            "Terminologia Grupo competitivo",
            'title="Grupo competitivo"' in page,
        ),
        (
            "Contexto não usa Por que esta referência",
            "Por que esta referência?" not in page,
        ),
        (
            "Contexto usa Entenda seu grupo competitivo",
            "Entenda seu grupo competitivo" in page,
        ),
        (
            "Especialista não é descrito como próximo elo",
            "Isso não significa que" in page
            and "seja seu próximo elo" in page,
        ),
        (
            "Coach mostra foco compacto primeiro",
            "_render_compact_training(" in coach_block,
        ),
        (
            "Coach não renderiza treino completo direto",
            "_render_training_mission(" not in coach_block,
        ),
        (
            "Coach tem próxima partida",
            "Próxima partida" in coach_block,
        ),
        (
            "Leitura completa fica recolhida",
            "Ver leitura completa do Coach" in coach_block,
        ),
        (
            "Missão e checklist ficam recolhidos",
            "Ver missão e checklist" in coach_block,
        ),
        (
            "Inteligência adaptativa fica recolhida",
            "Ver inteligência adaptativa" in coach_block,
        ),
        (
            "Evolução fica recolhida",
            "Ver evolução e histórico" in coach_block,
        ),
        (
            "Ollama prioriza ação",
            "recomendação acionável" in narrator,
        ),
        (
            "Ollama evita despejo de métricas",
            "não comece despejando todas as métricas" in narrator,
        ),
        (
            "Ollama não repete Spectrum",
            "Não repita a posição do Spectrum" in narrator,
        ),
        (
            "Proteção de promoção continua",
            "requisito de promoção" in narrator,
        ),
    ]

    print("=" * 84)
    print("TFT INSIGHT - UI + COACH SPECTRUM HOTFIX V1.1")
    print("=" * 84)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        1,
    ):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 84)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "UI + COACH SPECTRUM HOTFIX V1.1: VALIDADO"
        )
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
