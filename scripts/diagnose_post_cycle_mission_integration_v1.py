from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(
    PROJECT_ROOT / ".env"
)

from src.riot_client import RiotClient
from src.storage import PlayerRepository
from src.training.models.training_plan import (
    TrainingExercise,
    TrainingPlan,
)
from src.training.services.player_training_service import (
    PlayerTrainingService,
)


def build_plan(
    skill_id: str,
) -> TrainingPlan:
    labels = {
        "leveling": "Leveling",
        "consistency": "Consistência",
    }

    return TrainingPlan(
        primary_skill_id=skill_id,
        primary_skill_label=labels.get(
            skill_id,
            skill_id,
        ),
        objective=(
            "Validar a integração da decisão pós-ciclo."
        ),
        games_target=5,
        exercise=TrainingExercise(
            exercise_id="diagnostic_placeholder",
            title="Diagnóstico",
            instruction="Diagnóstico",
            checklist=("Diagnóstico",),
            success_signals=("Diagnóstico",),
            system_verification="Diagnóstico",
        ),
        secondary_focus=(),
        strengths_to_preserve=(),
        contexts_to_watch=(),
        rationale="Diagnóstico",
        confidence=90.0,
        limitations=(),
    )


def main() -> None:
    print("=" * 82)
    print(
        "TFT INSIGHT - POST-CYCLE MISSION INTEGRATION V1 - REAL"
    )
    print("=" * 82)

    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    priority_skill_id = input(
        "Skill prioritária atual [leveling]: "
    ).strip() or "leveling"

    riot_client = RiotClient()

    account = riot_client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    puuid = str(
        account.get(
            "puuid",
            "",
        )
    )

    if not puuid:
        raise RuntimeError(
            "PUUID não retornado pela Riot."
        )

    match_ids = tuple(
        riot_client.get_match_ids(
            puuid=puuid,
            count=30,
        )
    )

    repository = PlayerRepository()

    before = repository.load_training_mission(
        puuid=puuid
    )

    print()
    print("=" * 82)
    print("ANTES DA INTEGRAÇÃO")
    print("=" * 82)

    if before is None:
        print("Missão atual: ausente")
    else:
        print(
            f"Skill      : {before.skill_id}"
        )
        print(
            f"Task       : {before.task.id}"
        )
        print(
            f"Progresso  : "
            f"{before.games_completed}/"
            f"{before.games_target}"
        )
        print(
            f"Concluída  : "
            f"{'Sim' if before.is_completed else 'Não'}"
        )

    service = PlayerTrainingService(
        player_repository=repository
    )

    mission = (
        service.get_or_create_mission_from_plan(
            puuid=puuid,
            training_plan=build_plan(
                priority_skill_id
            ),
            baseline_match_ids=match_ids,
        )
    )

    print()
    print("=" * 82)
    print("DEPOIS DA INTEGRAÇÃO")
    print("=" * 82)
    print(
        f"Skill      : {mission.skill_id}"
    )
    print(
        f"Task       : {mission.task.id}"
    )
    print(
        f"Título     : {mission.title}"
    )
    print(
        f"Progresso  : "
        f"{mission.games_completed}/"
        f"{mission.games_target}"
    )
    print(
        f"Baseline   : "
        f"{len(mission.baseline_match_ids)} partidas"
    )
    print(
        f"Concluída  : "
        f"{'Sim' if mission.is_completed else 'Não'}"
    )

    print()
    print("=" * 82)
    print("VALIDAÇÃO ESPERADA")
    print("=" * 82)
    print(
        "No cenário atual, após Consistency 5/5 e prioridade Leveling:"
    )
    print(
        "Skill esperada : leveling"
    )
    print(
        "Task esperada  : plan_level_before_spending"
    )
    print(
        "Progresso      : 0/5"
    )
    print(
        "O baseline deve usar as partidas atuais, "
        "sem contar partidas antigas retroativamente."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'ANTES DA INTEGRAÇÃO' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
