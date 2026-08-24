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
from src.training.services.anti_loop_training_guard import (
    AntiLoopTrainingGuard,
)


def main() -> None:
    print("=" * 82)
    print(
        "TFT INSIGHT - ANTI-LOOP TRAINING GUARD V1 - REAL"
    )
    print("=" * 82)

    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    skill_id = input(
        "Skill para avaliar [leveling]: "
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

    repository = PlayerRepository()

    cycles = repository.list_training_cycles(
        puuid=puuid
    )

    decision = AntiLoopTrainingGuard.evaluate(
        skill_id=skill_id,
        training_history=cycles,
    )

    print()
    print("=" * 82)
    print("DECISÃO ANTI-LOOP")
    print("=" * 82)
    print(
        f"Skill                 : {decision.skill_id}"
    )
    print(
        f"Ação                  : {decision.action}"
    )
    print(
        f"Progressão da task    : {decision.task_progression}"
    )
    print(
        f"Tendência             : {decision.trend}"
    )
    print(
        f"Confiança tendência   : {decision.trend_confidence}"
    )
    print(
        f"Ciclos consecutivos   : {decision.consecutive_skill_cycles}"
    )
    print(
        f"Ciclos avaliados      : {decision.evaluated_cycles}"
    )
    print(
        f"Ciclos conclusivos    : {decision.conclusive_cycles}"
    )
    print(
        "Resultados recentes   : "
        + (
            ", ".join(
                decision.recent_results
            )
            if decision.recent_results
            else "-"
        )
    )

    print()
    print("MOTIVO")
    print(
        decision.rationale
    )

    print()
    print("CAUTELA")
    print(
        decision.caution
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "Esta V1 ainda NÃO interfere no Learning Priority Engine nem cria "
        "automaticamente uma task mais difícil."
    )
    print(
        "ADVANCE_CANDIDATE é apenas um sinal de que a Skill pode receber "
        "progressão quando adicionarmos dificuldade formal ao catálogo."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'DECISÃO ANTI-LOOP' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
