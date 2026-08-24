from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(
    PROJECT_ROOT / ".env"
)

from src.progress_intelligence import (
    ProgressHistoryService,
    ProgressMilestoneService,
    ProgressSnapshotService,
)
from src.riot_client import RiotClient
from src.storage import PlayerRepository


def main():
    print("=" * 82)
    print("TFT INSIGHT - FASE 12.1 A 12.3 - DIAGNÓSTICO REAL V1.1")
    print("=" * 82)

    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    if not game_name or not tag_line:
        raise RuntimeError(
            "Riot ID e Tag são obrigatórios."
        )

    print()
    print("[1] Resolvendo conta Riot...")

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
    ).strip()

    if not puuid:
        raise RuntimeError(
            "PUUID não retornado pela Riot."
        )

    print("[OK] Conta resolvida")

    print()
    print("[2] Resolvendo diretório persistido...")

    repo = PlayerRepository()

    player_dir = repo.get_player_directory(
        puuid=puuid
    )

    print(
        f"[OK] Diretório: {player_dir}"
    )

    profile_path = (
        player_dir
        / "learning"
        / "learning_profile.json"
    )

    if not profile_path.exists():
        raise RuntimeError(
            "Learning Profile não encontrado no diretório real do jogador: "
            f"{profile_path}"
        )

    print("[OK] Learning Profile encontrado")

    print()
    print("[3] Carregando estado longitudinal...")

    profile = json.loads(
        profile_path.read_text(
            encoding="utf-8"
        )
    )

    cycles = repo.list_training_cycles(
        puuid=puuid
    )

    history_before = (
        ProgressHistoryService.load(
            player_directory=player_dir
        )
    )

    previous = (
        history_before[-1]
        if history_before
        else None
    )

    print(
        f"[OK] Snapshots existentes: {len(history_before)}"
    )
    print(
        f"[OK] Ciclos arquivados: {len(cycles)}"
    )

    print()
    print("[4] Criando snapshot atual...")

    snapshot = (
        ProgressSnapshotService.build(
            learning_profile=profile,
            archived_cycles_total=len(
                cycles
            ),
            metadata={
                "diagnostic": (
                    "phase12_1_to_12_3_v1_1"
                ),
                "riot_id": game_name,
                "tag": tag_line,
            },
        )
    )

    persisted = (
        ProgressHistoryService.append(
            player_directory=player_dir,
            snapshot=snapshot,
        )
    )

    milestones = (
        ProgressMilestoneService.detect(
            previous=previous,
            current=snapshot,
        )
    )

    history_after = (
        ProgressHistoryService.load(
            player_directory=player_dir
        )
    )

    print("[OK] Snapshot processado")

    print()
    print("=" * 82)
    print("PROGRESS SNAPSHOT")
    print("=" * 82)
    print(
        f"Jogador            : {game_name}#{tag_line}"
    )
    print(
        f"Snapshot ID        : {snapshot.snapshot_id}"
    )
    print(
        f"Criado em          : {snapshot.created_at}"
    )
    print(
        f"Prioridade         : {snapshot.priority_skill_id or '-'}"
    )
    print(
        f"Skills             : {len(snapshot.skills)}"
    )
    print(
        f"Ciclos arquivados  : {snapshot.archived_cycles_total}"
    )
    print(
        "Persistido agora   : "
        f"{'Sim' if persisted else 'Não (já existia)'}"
    )

    for skill_id, skill in (
        snapshot.skills.items()
    ):
        print()
        print(f"{skill_id}:")
        print(
            f"  Score       : "
            f"{skill.get('score') if skill.get('score') is not None else '-'}"
        )
        print(
            f"  Nível       : "
            f"{skill.get('level')}"
        )
        print(
            f"  Tendência   : "
            f"{skill.get('trend')}"
        )
        print(
            f"  Dificuldade : "
            f"{skill.get('current_difficulty') or '-'}"
        )

    print()
    print("=" * 82)
    print("HISTÓRICO LONGITUDINAL")
    print("=" * 82)
    print(
        f"Antes : {len(history_before)} snapshot(s)"
    )
    print(
        f"Depois: {len(history_after)} snapshot(s)"
    )

    print()
    print("=" * 82)
    print("MILESTONES OBSERVADOS")
    print("=" * 82)

    if not milestones:
        print(
            "Nenhum novo milestone entre os snapshots disponíveis."
        )
    else:
        for item in milestones:
            print(
                f"{item.skill_id} | "
                f"{item.milestone_type} | "
                f"{item.from_value} -> "
                f"{item.to_value}"
            )

    print()
    print("=" * 82)
    print("CAMINHO DA PERSISTÊNCIA")
    print("=" * 82)
    print(
        ProgressHistoryService.path_for(
            player_directory=player_dir
        )
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "O Riot ID foi convertido para o PUUID real antes do acesso ao PlayerRepository."
    )
    print(
        "O diretório do jogador é derivado pelo próprio PlayerRepository; "
        "não informe hash de pasta manualmente."
    )
    print(
        "Elo não participa do cálculo de progresso."
    )
    print(
        "O snapshot preserva o Learning Profile e não recalcula Skills."
    )
    print(
        "Milestones descrevem mudanças observadas entre snapshots."
    )
    print(
        "Nenhum milestone altera Learning Priority, missão ou Adaptive Coach."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'PROGRESS SNAPSHOT' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
