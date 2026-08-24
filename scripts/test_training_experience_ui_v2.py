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
            "9.5 possui experiência de ciclo concluído",
            'eyebrow="Ciclo concluído"' in source
            and "Pronto para transição" in source,
        ),
        (
            "9.5 esconde checklist após 5/5",
            "if checklist and not is_completed:" in source,
        ),
        (
            "9.5 evita exercício ativo após conclusão",
            "if not is_completed:" in source
            and 'eyebrow="Exercício atual"' in source,
        ),
        (
            "9.6 distingue prioridade durante ciclo",
            "Nova prioridade detectada" in source
            and "permanece protegida até o 5/5" in source,
        ),
        (
            "9.6 distingue transição após conclusão",
            "Próxima missão pronta para transição" in source,
        ),
        (
            "9.7 possui Before x After visual",
            "def _render_cycle_before_after(" in source
            and "**Before × After**" in source,
        ),
        (
            "9.7 mostra Before",
            'f"{label} · Before"' in source,
        ),
        (
            "9.7 mostra After",
            'f"{label} · After"' in source,
        ),
        (
            "9.7 mostra variação",
            '"Variação"' in source
            and "_training_delta_text(relative_change)" in source,
        ),
        (
            "9.8 usa um expander por ciclo",
            "for index, cycle in enumerate(" in source
            and "expander_title" in source,
        ),
        (
            "9.8 expanders ficam fechados",
            "expanded=False" in source,
        ),
        (
            "9.8 título resume ciclo",
            'f"{skill_name} · {title} · "' in source,
        ),
        (
            "Histórico mantém confiança",
            "confidence_score" in source,
        ),
        (
            "Histórico mantém reason",
            'evaluation.get(\n                        "reason"' in source,
        ),
        (
            "Histórico mantém caveat",
            'evaluation.get(\n                        "caveat"' in source,
        ),
        (
            "Mantém novo ciclo da 9.3",
            'eyebrow="Novo ciclo"' in source,
        ),
        (
            "Mantém progress dots",
            "_mission_progress_dots(" in source,
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - TRAINING EXPERIENCE UI V2 "
        "(FASES 9.5 A 9.8)"
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
            "TRAINING EXPERIENCE UI V2: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "TRAINING EXPERIENCE UI V2: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
