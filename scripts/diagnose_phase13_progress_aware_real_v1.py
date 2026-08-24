from __future__ import annotations
import sys
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
load_dotenv(ROOT/'.env')
from src.progress_intelligence.services.progress_history_service import ProgressHistoryService
from src.progress_intelligence.services.progress_intelligence_service import ProgressIntelligenceService
from src.progress_aware_coach import ProgressAwareCoachService
from src.riot_client import RiotClient
from src.storage import PlayerRepository

def main():
    print('='*82); print('TFT INSIGHT - FASE 13.1 A 13.4 - DIAGNÓSTICO REAL'); print('='*82)
    game=input('Riot ID (Game Name): ').strip(); tag=input('Tag: ').strip()
    account=RiotClient().get_account(game_name=game,tag_line=tag); puuid=str(account.get('puuid','')).strip()
    if not puuid: raise RuntimeError('PUUID não retornado pela Riot.')
    player_dir=PlayerRepository().get_player_directory(puuid=puuid)
    snapshots=ProgressHistoryService.load(player_directory=player_dir)
    if not snapshots: raise RuntimeError('Nenhum snapshot longitudinal encontrado.')
    priority=snapshots[-1].priority_skill_id
    progress=ProgressIntelligenceService.build(snapshots=snapshots,primary_skill_id=priority)
    result=ProgressAwareCoachService.build(progress=progress,priority_skill_id=priority,adaptive_strategy={})
    c=result['context']; s=result['strategy']
    print('\n'+'='*82); print('PROGRESS COACHING CONTEXT'); print('='*82)
    print(f"Skill                 : {c['skill_id']}")
    print(f"Snapshots             : {c['snapshot_count']}")
    print(f"Primeiro score        : {c['first_score']}")
    print(f"Score atual           : {c['latest_score']}")
    print(f"Delta                 : {c['delta']:+.2f}" if c['delta'] is not None else 'Delta                 : -')
    print(f"Direção recente       : {c['recent_direction']}")
    print(f"Sinal                 : {c['signal']}")
    print(f"Confiança             : {c['confidence']}")
    print(f"Movimentos consecut.  : {c['consecutive_moves']}")
    print(f"Reagir agora          : {'Sim' if c['enough_for_reaction'] else 'Não'}")
    print(f"Motivo                : {c['reason']}")
    print('\n'+'='*82); print('PROGRESS-AWARE STRATEGY'); print('='*82)
    print(f"Prioridade preservada : {s['priority_skill_id']}")
    print(f"Ação                  : {s['action']}")
    print(f"Confiança             : {s['confidence']}")
    print(f"Sinal de progresso    : {s['progress_signal']}")
    print(f"Motivo                : {s['rationale']}")
    print('\nIMPORTANTE')
    print('Com apenas 2 snapshots, uma queda grande continua sendo WATCH/OBSERVE.')
    print('A Fase 13 não troca Learning Priority, missão ou dificuldade automaticamente.')
    print('\n'+'='*82); print('DIAGNÓSTICO CONCLUÍDO'); print("Envie desde 'PROGRESS COACHING CONTEXT' até o final."); print('='*82)
if __name__=='__main__': main()
