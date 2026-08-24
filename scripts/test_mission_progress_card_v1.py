from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PAGE = (
    PROJECT_ROOT
    / "partner_platform"
    / "pages"
    / "benchmark_page.py"
)


def main() -> None:
    source = PAGE.read_text(
        encoding="utf-8"
    )

    ast.parse(source)

    checks = [
        (
            "Sintaxe válida",
            True,
        ),
        (
            "Possui progress dots",
            "def _mission_progress_dots(" in source,
        ),
        (
            "0/5 pode mostrar círculos vazios",
            '"○"' in source,
        ),
        (
            "Partidas concluídas usam círculos preenchidos",
            '"●"' in source,
        ),
        (
            "Possui estado Novo ciclo",
            '"Novo ciclo"' in source,
        ),
        (
            "Possui estado Em progresso",
            '"Em progresso"' in source,
        ),
        (
            "Possui estado Ciclo concluído",
            '"Ciclo concluído"' in source,
        ),
        (
            "Mostra progresso N/N",
            'f"### {completed}/{target} partidas"' in source,
        ),
        (
            "Checklist ganhou hierarquia visual",
            "Checklist para levar para a partida" in source,
        ),
        (
            "Mantém Training History",
            "def _render_training_history(" in source,
        ),
        (
            "Mantém Novo ciclo da Fase 9.1",
            "Histórico recente de" in source,
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 9.2 - MISSION PROGRESS CARD V1")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        start=1,
    ):
        passed += int(ok)

        print()
        print(f"[{index}] {name}")
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "MISSION PROGRESS CARD V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "MISSION PROGRESS CARD V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
