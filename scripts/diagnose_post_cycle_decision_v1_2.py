from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.riot_client import RiotClient
from src.storage import PlayerRepository
from src.training.services.post_cycle_decision_engine import (
    PostCycleDecisionEngine,
)


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - POST-CYCLE DECISION V1.2 - DIAGNÓSTICO REAL")
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

    if not game_name:
        raise ValueError(
            "Riot ID (Game Name) não pode ser vazio."
        )

    if not tag_line:
        raise ValueError(
            "Tag não pode ser vazia."
        )

    print()
    print("[1] Resolvendo conta Riot...")

    riot_client = RiotClient()

    account = riot_client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    if not isinstance(account, dict):
        raise RuntimeError(
            "RiotClient.get_account() não retornou um dicionário."
        )

    puuid = account.get(
        "puuid"
    )

    if not isinstance(
        puuid,
        str,
    ) or not puuid.strip():
        raise RuntimeError(
            "A Riot API não retornou um PUUID válido."
        )

    resolved_game_name = str(
        account.get(
            "gameName",
            game_name,
        )
        or game_name
    )

    resolved_tag_line = str(
        account.get(
            "tagLine",
            tag_line,
        )
        or tag_line
    )

    print("[OK] Conta resolvida")

    print()
    print("[2] Carregando estado persistido...")

    repository = PlayerRepository()

    player_directory = (
        repository.get_player_directory(
            puuid=puuid
        )
    )

    cycles = repository.list_training_cycles(
        puuid=puuid
    )

    current = repository.load_training_mission(
        puuid=puuid
    )

    print(
        f"[OK] Diretório: {player_directory.name}"
    )
    print(
        f"[OK] Ciclos arquivados: {len(cycles)}"
    )
    print(
        "[OK] Missão atual: "
        + (
            "encontrada"
            if current is not None
            else "não encontrada"
        )
    )

    completed_mission = None

    if (
        current is not None
        and current.is_completed
    ):
        completed_mission = current.to_dict()

    print()
    print("[3] Executando decisão pós-ciclo...")

    decision = PostCycleDecisionEngine.decide(
        priority_skill_id=priority_skill_id,
        completed_mission=completed_mission,
        training_history=cycles,
    )

    print("[OK] Decisão calculada")

    print()
    print("=" * 82)
    print("DECISÃO PÓS-CICLO")
    print("=" * 82)
    print(
        "Jogador          : "
        f"{resolved_game_name}#{resolved_tag_line}"
    )
    print(
        f"Ação             : {decision.action}"
    )
    print(
        f"Skill-alvo       : {decision.target_skill_id}"
    )
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
    print(
        f"Estratégia task  : {decision.task_strategy}"
    )
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
    print("ESTADO ENCONTRADO")
    print("=" * 82)
    print(
        f"Ciclos arquivados : {len(cycles)}"
    )
    print(
        "Missão atual      : "
        + (
            "concluída"
            if (
                current is not None
                and current.is_completed
            )
            else (
                "ativa"
                if current is not None
                else "ausente"
            )
        )
    )

    if current is not None:
        print(
            "Progresso atual   : "
            f"{current.games_completed}/"
            f"{current.games_target}"
        )
        print(
            "Skill atual       : "
            f"{current.task.skill_id}"
        )
        print(
            "Task atual        : "
            f"{current.task.id}"
        )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "O Riot ID foi convertido para o PUUID real antes do acesso "
        "ao PlayerRepository."
    )
    print(
        "O PostCycleDecisionEngine não escolhe a Skill prioritária; "
        "ele decide apenas como treinar a prioridade recebida."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'DECISÃO PÓS-CICLO' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
