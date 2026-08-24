from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.progress_intelligence.services.progress_history_service import ProgressHistoryService
from src.progress_intelligence.services.progress_intelligence_service import ProgressIntelligenceService
from src.progress_aware_coach import ProgressAwareCoachService
from src.riot_client import RiotClient
from src.storage import PlayerRepository


def main():
    print("=" * 82)
    print("TFT INSIGHT - FASE 13.8 - END-TO-END REAL")
    print("=" * 82)

    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()

    account = RiotClient().get_account(
        game_name=game_name,
        tag_line=tag_line,
    )
    puuid = str(account.get("puuid", "")).strip()
    if not puuid:
        raise RuntimeError("PUUID não retornado pela Riot.")

    player_dir = PlayerRepository().get_player_directory(puuid=puuid)
    snapshots = ProgressHistoryService.load(player_directory=player_dir)
    if not snapshots:
        raise RuntimeError("Nenhum snapshot longitudinal encontrado.")

    priority = snapshots[-1].priority_skill_id
    progress = ProgressIntelligenceService.build(
        snapshots=snapshots,
        primary_skill_id=priority,
    )

    result = ProgressAwareCoachService.build(
        progress=progress,
        priority_skill_id=priority,
        adaptive_strategy={
            "current_task_id": "plan_level_before_spending",
            "current_difficulty": "FOUNDATION",
        },
    )

    context = result["context"]
    strategy = result["strategy"]
    adaptation = result["adaptation"]
    explanation = result["explanation"]

    print()
    print("=" * 82)
    print("FASE 13 - ESTADO END-TO-END REAL")
    print("=" * 82)
    print(f"Jogador              : {game_name}#{tag_line}")
    print(f"Snapshots             : {context['snapshot_count']}")
    print(f"Prioridade            : {strategy['priority_skill_id']}")
    print(f"Primeiro score        : {context['first_score']}")
    print(f"Score atual           : {context['latest_score']}")
    if context["delta"] is None:
        print("Delta                 : -")
    else:
        print(f"Delta                 : {context['delta']:+.2f}")
    print(f"Direção recente       : {context['recent_direction']}")
    print(f"Sinal longitudinal    : {context['signal']}")
    print(f"Confiança             : {context['confidence']}")
    print(f"Reagir agora          : {'Sim' if context['enough_for_reaction'] else 'Não'}")
    print(f"Reação do coach       : {strategy['action']}")
    print(f"Modo de treino        : {adaptation['mode']}")
    print(f"Task                  : {adaptation['task_id']}")
    print(f"Dificuldade           : {adaptation['difficulty']}")
    print(f"Muda missão           : {'Sim' if adaptation['changes_mission'] else 'Não'}")
    print(f"Muda prioridade       : {'Sim' if adaptation['changes_priority'] else 'Não'}")
    print(f"Muda dificuldade      : {'Sim' if adaptation['changes_difficulty'] else 'Não'}")

    print()
    print("EXPLICAÇÃO")
    print(f"Título: {explanation['title']}")
    print(explanation["summary"])
    print()
    print("Próximo passo:")
    print(explanation["next_step"])

    print()
    print("=" * 82)
    print("PIPELINE")
    print("=" * 82)
    print(
        "Performance -> Learning Profile -> Progress History -> "
        "Progress Intelligence -> Progress-Aware Context -> "
        "Strategy -> Training Adaptation -> Explanation -> UI"
    )

    print()
    print("=" * 82)
    print("PROTEÇÕES")
    print("=" * 82)
    print("Learning Priority continua escolhendo a Skill.")
    print("Learning Loop continua controlando missão e dificuldade.")
    print("Progress-Aware Coach decide apenas COMO reagir ao histórico.")
    print("Este diagnóstico é somente leitura e não cria novo snapshot.")

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'FASE 13 - ESTADO END-TO-END REAL' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
