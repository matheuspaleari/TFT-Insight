from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.progress_aware_coach import ProgressAwareCoachService

def progress(scores): return {"timelines":{"leveling":[{"score":x,"level":"BEGINNER"} for x in scores]}}
def run(scores): return ProgressAwareCoachService.build(progress=progress(scores),priority_skill_id="leveling",adaptive_strategy={"current_task_id":"plan_level_before_spending","current_difficulty":"FOUNDATION"})
checks=[]
a=run([15.22,3.08]); checks += [("WATCH preservado",a["context"]["signal"]=="WATCH"),("OBSERVE preservado",a["strategy"]["action"]=="OBSERVE"),("13.5 mantém treino",a["adaptation"]["mode"]=="KEEP_AND_OBSERVE"),("13.5 não muda missão",not a["adaptation"]["changes_mission"]),("13.5 não muda prioridade",not a["adaptation"]["changes_priority"]),("13.5 não muda dificuldade",not a["adaptation"]["changes_difficulty"]),("13.6 possui título",bool(a["explanation"]["title"])),("13.6 possui próximo passo",bool(a["explanation"]["next_step"])),("13.6 possui evidências",len(a["explanation"]["evidence"])==4),("13.6 possui limitações",len(a["explanation"]["limitations"])==3)]
b=run([15.22,10,3.08]); checks += [("regressão reforça",b["adaptation"]["mode"]=="REINFORCE"),("regressão não troca task",b["adaptation"]["task_id"]=="plan_level_before_spending")]
c=run([3.08,9.4,17.2]); checks += [("melhora prepara progressão",c["adaptation"]["mode"]=="PREPARE_PROGRESSION"),("melhora não avança difficulty",c["adaptation"]["difficulty"]=="FOUNDATION")]
page=(ROOT/'partner_platform/pages/benchmark_page.py').read_text(encoding='utf-8'); route=(ROOT/'src/integration_engine/api/routes/benchmark.py').read_text(encoding='utf-8'); contract=(ROOT/'src/integration_engine/contracts/benchmark.py').read_text(encoding='utf-8')
for x in (page,route,contract): ast.parse(x)
checks += [("13.7 API publica payload",'comparison_data["progress_aware_coach"]' in route),("13.7 contrato expõe payload",'progress_aware_coach: BenchmarkProgressAwareCoach' in contract),("13.7 UI possui seção",'Coach acompanhando sua evolução' in page),("13.7 UI consome payload",'comparison.get("progress_aware_coach")' in page),("UI mantém Sua evolução",'Sua evolução' in page),("UI mantém Adaptive Coach",'Inteligência adaptativa do coach' in page),("API mantém Progress Dashboard",'comparison_data["progress"]' in route),("prioridade vem pronta",'priority_skill_id=priority_skill_id' in route)]
print('='*82); print('TFT INSIGHT - FASE 13.5 A 13.7 - TRAINING ADAPTATION + UI V1'); print('='*82); passed=0
for i,(name,ok) in enumerate(checks,1): passed+=int(ok); print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
print('\n'+'='*82); print(f'PASSARAM: {passed}/{len(checks)}')
if passed==len(checks): print('FASE 13.5-13.7 TRAINING ADAPTATION + UI V1: VALIDADA'); raise SystemExit(0)
print('FASE 13.5-13.7: AJUSTE NECESSÁRIO'); raise SystemExit(1)
