from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.knowledge import get_tasks_for_skill
from src.training.services.task_difficulty_progression_engine import (
    TaskDifficultyProgressionEngine,
)


def main() -> None:
    print("=" * 82)
    print(
        "TFT INSIGHT - TASK DIFFICULTY + PROGRESSION V1 - DIAGNÓSTICO"
    )
    print("=" * 82)

    skill_id = input(
        "Skill [leveling]: "
    ).strip() or "leveling"

    tasks = tuple(
        get_tasks_for_skill(
            skill_id
        )
    )

    print()
    print("=" * 82)
    print("CATÁLOGO DA SKILL")
    print("=" * 82)

    for task in tasks:
        print(
            f"{task.difficulty:12} | "
            f"{task.id:32} | "
            f"{task.title}"
        )

    current_task_id = input(
        "\nTask atual [plan_level_before_spending]: "
    ).strip() or "plan_level_before_spending"

    signal = input(
        "Sinal [HOLD]: "
    ).strip().upper() or "HOLD"

    decision = (
        TaskDifficultyProgressionEngine.decide(
            skill_id=skill_id,
            current_task_id=current_task_id,
            progression_signal=signal,
        )
    )

    print()
    print("=" * 82)
    print("DECISÃO DE PROGRESSÃO")
    print("=" * 82)
    print(
        f"Skill                  : {decision.skill_id}"
    )
    print(
        f"Sinal                  : {decision.progression_signal}"
    )
    print(
        f"Task atual             : {decision.current_task_id}"
    )
    print(
        f"Dificuldade atual      : {decision.current_difficulty}"
    )
    print(
        f"Task selecionada       : {decision.selected_task_id}"
    )
    print(
        f"Dificuldade selecionada: {decision.selected_difficulty}"
    )
    print(
        f"Task mudou             : {'Sim' if decision.changed_task else 'Não'}"
    )
    print(
        f"Dificuldade mudou      : {'Sim' if decision.changed_difficulty else 'Não'}"
    )

    print()
    print("MOTIVO")
    print(
        decision.rationale
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "Esta etapa formaliza dificuldade e seleção de task, mas ainda "
        "não altera automaticamente o PostCycleDecisionEngine."
    )
    print(
        "A Skill continua sendo definida fora deste engine."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'CATÁLOGO DA SKILL' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
