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
 print('='*82); print('TFT INSIGHT - FASE 13.5 A 13.7 - DIAGNÓSTICO REAL'); print('='*82)
 game=input('Riot ID (Game Name): ').strip(); tag=input('Tag: ').strip(); account=RiotClient().get_account(game_name=game,tag_line=tag); puuid=str(account.get('puuid','')).strip(); player_dir=PlayerRepository().get_player_directory(puuid=puuid); snaps=ProgressHistoryService.load(player_directory=player_dir); priority=snaps[-1].priority_skill_id; progress=ProgressIntelligenceService.build(snapshots=snaps,primary_skill_id=priority); result=ProgressAwareCoachService.build(progress=progress,priority_skill_id=priority,adaptive_strategy={"current_task_id":"plan_level_before_spending","current_difficulty":"FOUNDATION"}); c=result['context']; s=result['strategy']; a=result['adaptation']; e=result['explanation']
 print('\n'+'='*82); print('TRAINING ADAPTATION'); print('='*82); print(f"Skill preservada      : {s['priority_skill_id']}"); print(f"Sinal                 : {c['signal']}"); print(f"Confiança             : {c['confidence']}"); print(f"Reação                : {s['action']}"); print(f"Modo de treino        : {a['mode']}"); print(f"Task                  : {a['task_id']}"); print(f"Dificuldade           : {a['difficulty']}"); print(f"Muda missão           : {'Sim' if a['changes_mission'] else 'Não'}"); print(f"Muda prioridade       : {'Sim' if a['changes_priority'] else 'Não'}"); print(f"Muda dificuldade      : {'Sim' if a['changes_difficulty'] else 'Não'}"); print(f"Orientação            : {a['instruction']}")
 print('\n'+'='*82); print('PROGRESS-AWARE EXPLANATION'); print('='*82); print(f"Título                : {e['title']}"); print(e['summary']); print('\nPróximo passo:'); print(e['next_step']); print('\nIMPORTANTE'); print('Com 2 snapshots atuais, o esperado continua WATCH / OBSERVE / KEEP_AND_OBSERVE.'); print('A UI deve exibir a nova seção Coach acompanhando sua evolução.'); print('\n'+'='*82); print('DIAGNÓSTICO CONCLUÍDO'); print("Envie desde 'TRAINING ADAPTATION' até o final."); print('='*82)
if __name__=='__main__': main()
