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
from src.training.services.learning_loop_orchestrator import (
    LearningLoopOrchestrator,
)
from src.training.services.pedagogical_memory_service import (
    PedagogicalMemoryService,
)


def main() -> None:
    print("=" * 82)
    print(
        "TFT INSIGHT - FASE 10.5/10.6/10.7 - DIAGNÓSTICO REAL"
    )
    print("=" * 82)

    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    priority_skill_id = input(
        "Prioridade atual [leveling]: "
    ).strip() or "leveling"

    riot = RiotClient()

    account = riot.get_account(
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

    repo = PlayerRepository()

    history = repo.list_training_cycles(
        puuid=puuid
    )

    current = repo.load_training_mission(
        puuid=puuid
    )

    memory_service = PedagogicalMemoryService(
        player_repository=repo
    )

    memory = memory_service.refresh(
        puuid=puuid,
        training_history=history,
        current_mission=current,
    )

    completed = (
        current.to_dict()
        if (
            current is not None
            and current.is_completed
        )
        else None
    )

    decision = LearningLoopOrchestrator.decide(
        priority_skill_id=priority_skill_id,
        completed_mission=completed,
        training_history=history,
    )

    print()
    print("=" * 82)
    print("LEARNING LOOP")
    print("=" * 82)
    print(
        f"Prioridade            : {decision.priority_skill_id}"
    )
    print(
        f"Post-Cycle            : {decision.post_cycle_action}"
    )
    print(
        f"Anti-Loop             : {decision.anti_loop_action}"
    )
    print(
        f"Sinal de progressão   : {decision.progression_signal}"
    )
    print(
        f"Tendência             : {decision.trend}"
    )
    print(
        f"Confiança tendência   : {decision.trend_confidence}"
    )
    print(
        f"Task selecionada      : {decision.selected_task_id or '-'}"
    )
    print(
        f"Dificuldade           : {decision.selected_difficulty or '-'}"
    )
    print(
        f"Ciclos consecutivos   : {decision.consecutive_skill_cycles}"
    )
    print(
        f"Reavaliar prioridade  : "
        f"{'Sim' if decision.requires_priority_reassessment else 'Não'}"
    )
    print(
        f"Adiar nova missão     : "
        f"{'Sim' if decision.defer_new_mission else 'Não'}"
    )

    print()
    print("MOTIVO")
    print(
        decision.rationale
    )

    print()
    print("=" * 82)
    print("MEMÓRIA PEDAGÓGICA")
    print("=" * 82)
    print(
        "Arquivo: "
        + str(
            repo.get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "pedagogical_memory.json"
        )
    )

    for skill_id, state in (
        memory.get(
            "skills",
            {}
        ).items()
    ):
        print()
        print(
            f"{skill_id}:"
        )
        print(
            f"  ciclos        : {state['cycles_total']}"
        )
        print(
            f"  conclusivos   : {state['conclusive_cycles']}"
        )
        print(
            f"  tendência     : {state['trend']}"
        )
        print(
            f"  anti-loop     : {state['anti_loop_action']}"
        )
        print(
            f"  progressão    : {state['task_progression']}"
        )
        print(
            f"  dificuldade   : {state.get('current_difficulty') or '-'}"
        )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "Este diagnóstico atualiza apenas pedagogical_memory.json. "
        "Ele não cria nem substitui a missão atual."
    )
    print(
        "Learning Priority continua responsável por escolher a Skill; "
        "o Learning Loop decide somente como treiná-la."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'LEARNING LOOP' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
