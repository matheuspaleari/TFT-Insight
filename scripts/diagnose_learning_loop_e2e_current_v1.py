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
        "TFT INSIGHT - FASE 10.8 - ESTADO REAL ATUAL"
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

    current = repo.load_training_mission(
        puuid=puuid
    )

    history = repo.list_training_cycles(
        puuid=puuid
    )

    decision = (
        LearningLoopOrchestrator.decide(
            priority_skill_id=priority_skill_id,
            completed_mission=(
                current.to_dict()
                if (
                    current is not None
                    and current.is_completed
                )
                else None
            ),
            training_history=history,
        )
    )

    memory = repo.load_pedagogical_memory(
        puuid=puuid
    )

    print()
    print("=" * 82)
    print("ESTADO END-TO-END")
    print("=" * 82)

    if current is None:
        print(
            "Missão atual          : ausente"
        )
    else:
        print(
            f"Missão atual          : "
            f"{current.skill_id} / {current.task.id}"
        )
        print(
            f"Dificuldade atual     : "
            f"{getattr(current.task, 'difficulty', 'FOUNDATION')}"
        )
        print(
            f"Progresso             : "
            f"{current.games_completed}/{current.games_target}"
        )

    print(
        f"Ciclos arquivados     : {len(history)}"
    )
    print(
        f"Prioridade recebida   : {decision.priority_skill_id}"
    )
    print(
        f"Tendência             : {decision.trend}"
    )
    print(
        f"Anti-Loop             : {decision.anti_loop_action}"
    )
    print(
        f"Progressão            : {decision.progression_signal}"
    )
    print(
        f"Task sugerida         : {decision.selected_task_id or '-'}"
    )
    print(
        f"Dificuldade sugerida  : {decision.selected_difficulty or '-'}"
    )
    print(
        f"Adiar nova missão     : "
        f"{'Sim' if decision.defer_new_mission else 'Não'}"
    )

    print()
    print("MEMÓRIA")
    print(
        "Persistida            : "
        f"{'Sim' if isinstance(memory, dict) else 'Não'}"
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "Este diagnóstico é somente leitura e não cria uma nova missão."
    )
    print(
        "O teste determinístico test_learning_loop_e2e_v1.py é o que "
        "valida os cenários completos sem depender de jogar várias partidas."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'ESTADO END-TO-END' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
