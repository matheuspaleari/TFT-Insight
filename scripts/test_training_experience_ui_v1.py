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
        (
            "Arquivo possui sintaxe válida",
            True,
        ),
        (
            "UI identifica novo ciclo em 0/N",
            "is_new_cycle = (" in source
            and "completed == 0" in source,
        ),
        (
            "UI consulta histórico da mesma Skill",
            "_find_latest_training_cycle_for_skill" in source,
        ),
        (
            "UI mostra resultado anterior",
            "_training_result_summary" in source,
        ),
        (
            "UI explica rotação de exercício",
            "o exercício foi rotacionado" in source,
        ),
        (
            "Checklist usa caixas visuais",
            'f"☐ {item}"' in source,
        ),
        (
            "Missão ativa continua protegida na mensagem",
            "missão atual continua protegida até o fim do ciclo" in source,
        ),
        (
            "Ciclo concluído não diz mais que ainda precisa terminar",
            "O ciclo atual já foi concluído." in source,
        ),
        (
            "UI mantém avaliação Before/After no histórico",
            "_render_training_history" in source
            and "_TRAINING_RESULT_LABELS" in source,
        ),
        (
            "UI continua sem recalcular prioridade",
            "A UI não recalcula prioridade" in source,
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - TRAINING EXPERIENCE UI V1"
    )
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        start=1,
    ):
        passed += int(ok)

        print()
        print(
            f"[{index}] {name}"
        )
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
            "TRAINING EXPERIENCE UI V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "TRAINING EXPERIENCE UI V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
