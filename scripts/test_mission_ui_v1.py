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
            "Helper da Mission UI existe",
            "def _render_training_mission(" in source,
        ),
        (
            "UI consome comparison['training']",
            'comparison.get("training")' in source,
        ),
        (
            "Progresso vem do backend",
            '"progress_percentage"' in source,
        ),
        (
            "Checklist vem do backend",
            '"checklist"' in source,
        ),
        (
            "Próximo foco respeita missão atual",
            '"current_priority_skill_id"' in source,
        ),
        (
            "UI não chama CoachEngine",
            "CoachEngine" not in source,
        ),
        (
            "UI não recalcula Learning Priority",
            "LearningPriorityEngine" not in source,
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - MISSION UI V1")
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
            "MISSION UI V1: ESTRUTURA VALIDADA"
        )
        raise SystemExit(0)

    print(
        "MISSION UI V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
