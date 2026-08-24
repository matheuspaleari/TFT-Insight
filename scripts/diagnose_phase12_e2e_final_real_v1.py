from __future__ import annotations

import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.progress_intelligence.services.progress_history_service import ProgressHistoryService
from src.progress_intelligence.services.progress_intelligence_service import ProgressIntelligenceService
from src.riot_client import RiotClient
from src.storage import PlayerRepository


def main():
    print("=" * 82)
    print("TFT INSIGHT - FASE 12.8 - END-TO-END REAL")
    print("=" * 82)
    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()

    account = RiotClient().get_account(game_name=game_name, tag_line=tag_line)
    puuid = str(account.get("puuid", "")).strip()
    if not puuid:
        raise RuntimeError("PUUID não retornado pela Riot.")

    player_dir = PlayerRepository().get_player_directory(puuid=puuid)
    snapshots = ProgressHistoryService.load(player_directory=player_dir)
    if not snapshots:
        raise RuntimeError("Nenhum snapshot longitudinal encontrado.")

    priority = snapshots[-1].priority_skill_id
    intel = ProgressIntelligenceService.build(
        snapshots=snapshots, primary_skill_id=priority
    )

    print("\n" + "=" * 82)
    print("FASE 12 - ESTADO END-TO-END REAL")
    print("=" * 82)
    print(f"Jogador              : {game_name}#{tag_line}")
    print(f"Snapshots             : {len(snapshots)}")
    print(f"Prioridade            : {priority}")
    print(f"Primeiro snapshot     : {snapshots[0].created_at}")
    print(f"Último snapshot       : {snapshots[-1].created_at}")

    print("\nSKILLS")
    for skill_id, points in intel["timelines"].items():
        first, latest = points[0], points[-1]
        a, b = first.get("score"), latest.get("score")
        delta = f"{b-a:+.2f}" if isinstance(a, (int,float)) and isinstance(b, (int,float)) else "-"
        print(f"{skill_id:16} | {a} -> {b} | delta={delta} | nível={latest.get('level')}")

    overall = intel["overall_development"]
    print("\nDESENVOLVIMENTO")
    print(f"Status                : {overall['status']}")
    print(f"Confiança             : {overall['confidence']}")
    print(f"Histórico insuficiente: {', '.join(overall['insufficient_skills']) or '-'}")

    print("\nINSIGHTS")
    for item in intel["insights"]:
        print(f"- [{item['role']}] {item['title']}")
        print(f"  {item['message']}")

    print("\n" + "=" * 82)
    print("PIPELINE VALIDADO")
    print("=" * 82)
    print("Learning Profile -> Progress Snapshot -> Progress History -> Skill Timeline -> Overall Development -> Progress Insights -> Dashboard")

    print("\nIMPORTANTE")
    print("Este diagnóstico é somente leitura.")
    print("Ele não cria snapshot, não altera missão e não muda Learning Priority.")

    print("\n" + "=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'FASE 12 - ESTADO END-TO-END REAL' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
