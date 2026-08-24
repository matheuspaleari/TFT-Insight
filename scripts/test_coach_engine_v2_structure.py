"""
Smoke test estrutural do CoachEngine V2.

Este teste não chama Riot/API. Ele valida que o arquivo contém
o novo pipeline e preserva o fallback legado.
"""

from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = (
    PROJECT_ROOT
    / "src"
    / "coach"
    / "engine"
    / "coach_engine.py"
)


def main() -> None:
    source = ENGINE_PATH.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)

    expected_tokens = (
        "BenchmarkCoachContextBuilder",
        "HabitEngine",
        "HabitSkillMappingService",
        "SkillEvidenceFusionService",
        "LearningPriorityEngine",
        "TrainingPlanEngine",
        "get_or_create_mission_from_plan",
        "LearningEngine.recommend",
        "get_or_create_mission",
    )

    tests = [
        (
            token,
            token in source,
        )
        for token in expected_tokens
    ]

    class_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }

    tests.append(
        (
            "CoachEngine",
            "CoachEngine" in class_names,
        )
    )

    print("=" * 82)
    print("TFT INSIGHT - COACH ENGINE V2 STRUCTURAL VALIDATION")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        tests,
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
        f"PASSARAM: {passed}/{len(tests)}"
    )

    if passed == len(tests):
        print(
            "COACH ENGINE V2: ESTRUTURA VALIDADA"
        )
        raise SystemExit(0)

    print(
        "COACH ENGINE V2: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
