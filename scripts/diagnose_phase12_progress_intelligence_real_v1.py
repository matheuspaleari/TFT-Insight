from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.progress_intelligence.services.progress_history_service import (
    ProgressHistoryService,
)
from src.progress_intelligence.services.progress_intelligence_service import (
    ProgressIntelligenceService,
)
from src.riot_client import RiotClient
from src.storage import PlayerRepository


def main():
    print("=" * 82)
    print("TFT INSIGHT - FASE 12.4 A 12.6 - DIAGNÓSTICO REAL")
    print("=" * 82)

    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()

    riot = RiotClient()
    account = riot.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )
    puuid = str(account.get("puuid", "")).strip()

    if not puuid:
        raise RuntimeError("PUUID não retornado pela Riot.")

    repo = PlayerRepository()
    player_dir = repo.get_player_directory(puuid=puuid)

    snapshots = ProgressHistoryService.load(
        player_directory=player_dir
    )

    if not snapshots:
        raise RuntimeError(
            "Nenhum progress snapshot encontrado. "
            "Rode primeiro o diagnóstico da Fase 12.1-12.3."
        )

    priority = snapshots[-1].priority_skill_id

    result = ProgressIntelligenceService.build(
        snapshots=snapshots,
        primary_skill_id=priority,
    )

    print()
    print("=" * 82)
    print("SKILL PROGRESS TIMELINE")
    print("=" * 82)

    for skill_id, points in result["timelines"].items():
        print()
        print(f"SKILL: {skill_id}")
        print(f"Snapshots: {len(points)}")
        first = points[0]
        latest = points[-1]
        print(f"Primeiro score : {first.get('score')}")
        print(f"Score atual    : {latest.get('score')}")
        print(f"Nível atual    : {latest.get('level')}")
        print(f"Tendência      : {latest.get('trend')}")

    print()
    print("=" * 82)
    print("OVERALL PLAYER DEVELOPMENT")
    print("=" * 82)

    summary = result["overall_development"]
    print(f"Status              : {summary['status']}")
    print(f"Confiança           : {summary['confidence']}")
    print(f"Skill prioritária   : {summary['primary_skill_id']}")
    print(f"Melhorando          : {', '.join(summary['improving_skills']) or '-'}")
    print(f"Estáveis            : {', '.join(summary['stable_skills']) or '-'}")
    print(f"Regredindo          : {', '.join(summary['regressing_skills']) or '-'}")
    print(f"Histórico insuf.    : {', '.join(summary['insufficient_skills']) or '-'}")
    print(f"Motivo              : {summary['rationale']}")

    print()
    print("=" * 82)
    print("PROGRESS INSIGHTS")
    print("=" * 82)

    for item in result["insights"]:
        print()
        print(f"[{item['role']}] {item['title']}")
        print(item["message"])

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print("Esta fase lê progress_history.json e não cria novo snapshot.")
    print("O status geral não é média simples de scores.")
    print("Insights descrevem evolução observada; não alteram prioridade ou missão.")
    print("Com apenas 1 snapshot real, histórico insuficiente é o resultado esperado.")

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'SKILL PROGRESS TIMELINE' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
