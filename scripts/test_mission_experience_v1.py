from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

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
        ("Sintaxe válida", True),
        (
            "Mantém três cards executivos",
            'title="Foco"' in source
            and 'title="Progresso"' in source
            and 'title="Restantes"' in source,
        ),
        (
            "Exercício atual virou protagonista",
            'eyebrow="Exercício atual"' in source,
        ),
        (
            "Novo ciclo foi compactado",
            "transition_description" in source
            and 'eyebrow="Novo ciclo"' in source,
        ),
        (
            "Resultado anterior entra na transição",
            "_training_result_summary(" in source,
        ),
        (
            "Rotação de task é explicada",
            "o exercício desta Skill foi rotacionado" in source,
        ),
        (
            "Mantém progress dots",
            "_mission_progress_dots(" in source,
        ),
        (
            "Remove texto duplicado da progress bar",
            "text=(" not in source[
                source.index("st.progress("):
                source.index("st.progress(") + 250
            ],
        ),
        (
            "Checklist fica aberto e direto",
            'with st.container(' in source
            and 'f"☐ {item}"' in source,
        ),
        (
            "Checklist não depende de interação",
            "não é necessário marcar nada" in source,
        ),
        (
            "Momento do ciclo fica compacto",
            'f"**{cycle_stage_label}:** "' in source,
        ),
        (
            "Momento inicial não duplica Novo ciclo",
            "and not is_new_cycle" in source,
        ),
        (
            "Histórico completo continua presente",
            "def _render_training_history(" in source,
        ),
        (
            "Before/After continua presente",
            "_TRAINING_RESULT_LABELS" in source
            and "_TRAINING_METRIC_LABELS" in source,
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - FASE 9.3 - MISSION EXPERIENCE V1"
    )
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
            "MISSION EXPERIENCE V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "MISSION EXPERIENCE V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
