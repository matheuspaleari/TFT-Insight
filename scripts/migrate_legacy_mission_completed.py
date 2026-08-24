"""
Migração manual única para uma missão antiga que já foi cumprida,
mas não teve as partidas contabilizadas.

Use somente quando você sabe que jogou pelo menos games_target partidas
depois de receber a missão antiga. O produto normal não faz essa inferência.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.services import PlayerAnalysisService
from src.training import PlayerTrainingService


def main() -> None:
    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()
    benchmark_id = input("Benchmark ID [advanced]: ").strip() or "advanced"
    match_count = int(input("Quantidade de partidas [30]: ").strip() or "30")

    analysis = PlayerAnalysisService().analyze(
        game_name=game_name,
        tag_line=tag_line,
        benchmark_id=benchmark_id,
        match_count=match_count,
        use_cache=True,
    )

    service = PlayerTrainingService()
    mission = service.player_repository.load_training_mission(
        puuid=analysis.puuid
    )

    if mission is None:
        print("Nenhuma missão ativa encontrada.")
        return

    print()
    print(f"Missão atual : {mission.title}")
    print(f"Progresso    : {mission.games_completed}/{mission.games_target}")
    print(f"Baseline     : {len(mission.baseline_match_ids)} IDs")

    if mission.is_completed:
        print("A missão já está concluída.")
        return

    confirmation = input(
        "\nSe você confirma que já jogou pelo menos "
        f"{mission.games_target} partidas após receber esta missão, "
        "digite CONCLUIR: "
    ).strip()

    if confirmation != "CONCLUIR":
        print("Migração cancelada.")
        return

    evidence_ids = tuple(
        analysis.match_ids[
            :mission.games_target
        ]
    )

    # Migração manual: esses IDs servem apenas como registro da confirmação.
    # O próximo ciclo terá baseline próprio e será rastreado automaticamente.
    completed = replace(
        mission,
        baseline_match_ids=(),
        completed_match_ids=evidence_ids,
        games_completed=len(evidence_ids),
    )

    service.player_repository.save_training_mission(
        puuid=analysis.puuid,
        mission=completed,
    )

    print()
    print(
        "Missão antiga marcada como concluída por migração manual: "
        f"{completed.games_completed}/{completed.games_target}"
    )
    print(
        "Rode novamente o diagnóstico E2E para o sistema criar "
        "a próxima missão com baseline automático."
    )


if __name__ == "__main__":
    main()
