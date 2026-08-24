from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.knowledge import (
    TRAINING_TASK_CATALOG,
    get_tasks_for_skill,
)


def print_task(task) -> None:
    print()
    print("-" * 80)
    print(f"ID          : {task.id}")
    print(f"Skill       : {task.skill_id}")
    print(f"Título      : {task.title}")
    print(f"Descrição   : {task.description}")
    print(f"Objetivo    : {task.objective}")
    print(f"Hábito      : {task.habit}")

    print()
    print("Checklist:")

    for item in task.checklist:
        print(f"  □ {item}")

    print()
    print("Sinais de sucesso:")

    for signal in task.success_signals:
        print(f"  ✓ {signal}")

    print()
    print("Erros comuns:")

    if task.common_mistakes:
        for mistake in task.common_mistakes:
            print(f"  • {mistake}")
    else:
        print("  Nenhum erro comum cadastrado.")

    print()
    print("Métricas relacionadas:")

    if task.related_metric_ids:
        for metric_id in task.related_metric_ids:
            print(f"  • {metric_id}")
    else:
        print("  Nenhuma métrica relacionada.")


def main() -> None:
    print()
    print("=" * 80)
    print("TFT INSIGHT - TRAINING TASK CATALOG")
    print("=" * 80)

    total_tasks = sum(
        len(tasks)
        for tasks in TRAINING_TASK_CATALOG.values()
    )

    print(f"Skills cadastradas : {len(TRAINING_TASK_CATALOG)}")
    print(f"Exercícios totais  : {total_tasks}")

    for skill_id, tasks in TRAINING_TASK_CATALOG.items():
        print()
        print("=" * 80)
        print(f"SKILL: {skill_id}")
        print(f"EXERCÍCIOS: {len(tasks)}")
        print("=" * 80)

        for task in tasks:
            print_task(task)

    print()
    print("=" * 80)
    print("TESTE DE BUSCA")
    print("=" * 80)

    leveling_tasks = get_tasks_for_skill(
        "leveling"
    )

    unknown_tasks = get_tasks_for_skill(
        "skill_inexistente"
    )

    print(
        f"Leveling retornou "
        f"{len(leveling_tasks)} exercícios."
    )

    print(
        f"Skill inexistente retornou "
        f"{len(unknown_tasks)} exercícios."
    )

    if total_tasks != 12:
        raise AssertionError(
            "O catálogo deveria possuir 12 exercícios."
        )

    if len(leveling_tasks) != 3:
        raise AssertionError(
            "Leveling deveria possuir 3 exercícios."
        )

    if unknown_tasks:
        raise AssertionError(
            "Uma Skill inexistente deveria retornar "
            "uma tupla vazia."
        )

    for skill_id, tasks in TRAINING_TASK_CATALOG.items():
        for task in tasks:
            if task.skill_id != skill_id:
                raise AssertionError(
                    f"O exercício {task.id!r} está cadastrado "
                    f"na Skill {skill_id!r}, mas informa "
                    f"skill_id={task.skill_id!r}."
                )

    print()
    print("✓ Catálogo validado com sucesso.")


if __name__ == "__main__":
    main()