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

    checks = [
        (
            "UI lê competitive spectrum",
            "def _analysis_spectrum(" in page,
        ),
        (
            "UI exibe barra do espectro",
            "def _render_spectrum_bar(" in page,
        ),
        (
            "UI usa Grupo competitivo",
            'title="Grupo competitivo"' in page,
        ),
        (
            "UI traduz EXPERT para Especialista",
            '"EXPERT": "Especialista"' in page,
        ),
        (
            "UI não destaca X/Y áreas",
            'áreas na ou acima da referência' not in page,
        ),
        (
            "UI separa perfil recente da posição",
            '"Seu perfil recente"' in page,
        ),
        (
            "UI traduz eliminações",
            '"average_players_eliminated": "Eliminações por partida"' in page,
        ),
        (
            "UI traduz consistência",
            '"placement_standard_deviation": "Consistência"' in page,
        ),
        (
            "Coach popup recebe spectrum",
            "spectrum=spectrum" in page,
        ),
        (
            "Narrador recebe competitive_spectrum",
            "competitive_spectrum: dict[str, Any] | None" in narrator,
        ),
        (
            "Narrador evita requisito de promoção",
            "requisito de promoção" in narrator,
        ),
        (
            "Narrador separa elo e perfil",
            "posição competitiva (elo) e perfil recente" in narrator,
        ),
        (
            "Narrador prefere grupo competitivo",
            '"grupo competitivo"' in narrator.lower(),
        ),
        (
            "Sem probability_to_rank_up",
            "probability_to_rank_up" not in page + narrator,
        ),
        (
            "Sem ready_to_rank_up",
            "ready_to_rank_up" not in page + narrator,
        ),
        (
            "Sem metrics_needed_to_rank_up",
            "metrics_needed_to_rank_up" not in page + narrator,
        ),
    ]

    print("=" * 84)
    print("TFT INSIGHT - UI + COACH SPECTRUM INTEGRATION V1")
    print("=" * 84)

    passed = 0

    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 84)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("UI + COACH SPECTRUM INTEGRATION V1: VALIDADO")
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
