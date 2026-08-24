from __future__ import annotations

import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.storage import PlayerRepository
from src.training.services.post_cycle_decision_engine import (
    PostCycleDecisionEngine,
)


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - POST-CYCLE DECISION V1 - DIAGNÓSTICO")
    print("=" * 82)

    puuid = input("PUUID hash/diretório do jogador: ").strip()
    priority_skill_id = input(
        "Skill prioritária atual [leveling]: "
    ).strip() or "leveling"

    repository = PlayerRepository()

    cycles = repository.list_training_cycles(
        puuid=puuid
    )

    current = repository.load_training_mission(
        puuid=puuid
    )

    completed_mission = None

    if (
        current is not None
        and current.is_completed
    ):
        completed_mission = current.to_dict()

    decision = PostCycleDecisionEngine.decide(
        priority_skill_id=priority_skill_id,
        completed_mission=completed_mission,
        training_history=cycles,
    )

    print()
    print("=" * 82)
    print("DECISÃO PÓS-CICLO")
    print("=" * 82)
    print(f"Ação             : {decision.action}")
    print(f"Skill-alvo       : {decision.target_skill_id}")
    print(
        "Skill concluída  : "
        f"{decision.previous_skill_id or '-'}"
    )
    print(
        "Resultado prévio : "
        f"{decision.previous_result or '-'}"
    )
    print(
        "Confiança prévia : "
        f"{decision.previous_confidence or '-'}"
    )
    print(f"Estratégia task  : {decision.task_strategy}")
    print(
        "Task anterior    : "
        f"{decision.previous_task_id or '-'}"
    )
    print(
        "Task sugerida    : "
        f"{decision.suggested_task_id or '-'}"
    )
    print(
        "Histórico usado  : "
        f"{'Sim' if decision.history_used else 'Não'}"
    )

    print()
    print("MOTIVO")
    print(decision.rationale)

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "Este engine NÃO escolheu a Skill prioritária. "
        "Ele recebeu a prioridade atual e decidiu apenas como "
        "transformá-la no próximo ciclo."
    )
    print(
        "A integração com MissionGenerator/CoachPipeline será feita "
        "somente depois desta decisão ser validada."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'DECISÃO PÓS-CICLO' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
