from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import PlayerRepository
from src.training.services.mission_generator import MissionGenerator
from src.training.services.player_training_service import PlayerTrainingService
from src.training.models.training_plan import TrainingExercise, TrainingPlan


def build_plan(
    *,
    skill_id: str,
    skill_label: str,
    exercise_id: str,
) -> TrainingPlan:
    return TrainingPlan(
        primary_skill_id=skill_id,
        primary_skill_label=skill_label,
        objective="Objetivo de teste",
        games_target=5,
        exercise=TrainingExercise(
            exercise_id=exercise_id,
            title="Exercício de teste",
            instruction="Instrução de teste",
            checklist=("Item",),
            success_signals=("Sinal",),
            system_verification="Parcial",
        ),
        secondary_focus=(),
        strengths_to_preserve=(),
        contexts_to_watch=(),
        rationale="Motivo de teste",
        confidence=90.0,
        limitations=(),
    )


def main() -> None:
    checks: list[tuple[str, bool]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        repo = PlayerRepository(
            players_directory=Path(temp_dir)
        )
        service = PlayerTrainingService(
            player_repository=repo
        )
        puuid = "player-history-test"

        baseline = tuple(
            f"old-{index}"
            for index in range(30)
        )

        leveling_plan = build_plan(
            skill_id="leveling",
            skill_label="Leveling",
            exercise_id="balance_level_and_stability",
        )

        next_plan = build_plan(
            skill_id="consistency",
            skill_label="Consistência",
            exercise_id="consistency_test",
        )

        mission = MissionGenerator.generate_from_plan(
            training_plan=leveling_plan,
            baseline_match_ids=baseline,
        )

        repo.save_training_mission(
            puuid=puuid,
            mission=mission,
        )

        current_match_ids = (
            "new-5",
            "new-4",
            "new-3",
            "new-2",
            "new-1",
            *baseline[:25],
        )

        completed = service.sync_mission_progress(
            puuid=puuid,
            current_match_ids=current_match_ids,
        )

        checks.append(
            (
                "Missão chegou a 5/5",
                completed is not None
                and completed.is_completed
                and completed.games_completed == 5,
            )
        )

        cycles = repo.list_training_cycles(
            puuid=puuid
        )

        checks.append(
            (
                "Ciclo foi arquivado",
                len(cycles) == 1,
            )
        )

        archived = cycles[0]

        checks.append(
            (
                "Histórico preserva mission_id",
                archived.get("cycle_id")
                == completed.mission_id,
            )
        )

        archived_mission = archived.get(
            "mission",
            {},
        )

        checks.append(
            (
                "Histórico preserva partidas do ciclo",
                archived_mission.get(
                    "completed_match_ids"
                )
                == list(
                    completed.completed_match_ids
                ),
            )
        )

        visible_completed = (
            service.get_or_create_mission_from_plan(
                puuid=puuid,
                training_plan=next_plan,
                baseline_match_ids=current_match_ids,
            )
        )

        checks.append(
            (
                "5/5 permanece visível na análise que concluiu",
                visible_completed.mission_id
                == completed.mission_id
                and visible_completed.is_completed,
            )
        )

        first_path = repo.archive_training_cycle(
            puuid=puuid,
            mission=completed,
        )
        second_path = repo.archive_training_cycle(
            puuid=puuid,
            mission=completed,
        )

        checks.append(
            (
                "Arquivamento é idempotente",
                first_path == second_path
                and len(
                    repo.list_training_cycles(
                        puuid=puuid
                    )
                )
                == 1,
            )
        )

        next_service = PlayerTrainingService(
            player_repository=repo
        )

        next_mission = (
            next_service.get_or_create_mission_from_plan(
                puuid=puuid,
                training_plan=next_plan,
                baseline_match_ids=current_match_ids,
            )
        )

        checks.append(
            (
                "Análise seguinte cria nova missão",
                next_mission.mission_id
                != completed.mission_id
                and not next_mission.is_completed,
            )
        )

        checks.append(
            (
                "Histórico continua com apenas um ciclo",
                len(
                    repo.list_training_cycles(
                        puuid=puuid
                    )
                )
                == 1,
            )
        )

        loaded_cycle = repo.load_training_cycle(
            puuid=puuid,
            cycle_id=completed.mission_id,
        )

        checks.append(
            (
                "Ciclo arquivado pode ser carregado",
                loaded_cycle is not None
                and loaded_cycle.get("status")
                == "completed",
            )
        )

    print("=" * 82)
    print("TFT INSIGHT - TRAINING CYCLE HISTORY V1")
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
            "TRAINING CYCLE HISTORY V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "TRAINING CYCLE HISTORY V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
