from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.progress_aware_coach import ProgressAwareCoachService

def progress(scores):
    return {"timelines":{"leveling":[{"score":x,"level":"BEGINNER"} for x in scores]}}

def run(scores):
    return ProgressAwareCoachService.build(progress=progress(scores), priority_skill_id="leveling", adaptive_strategy={"current_task_id":"plan_level_before_spending","current_difficulty":"FOUNDATION"})

cases=[]
a=run([15.22,3.08]); c=a["context"]; s=a["strategy"]
cases += [("2 snapshots = WATCH",c["signal"]=="WATCH"),("2 snapshots não reagem",not c["enough_for_reaction"]),("ação OBSERVE",s["action"]=="OBSERVE"),("delta -12.14",abs(c["delta"]+12.14)<.001)]
b=run([15.22,10.0,3.08]); c=b["context"]; s=b["strategy"]
cases += [("3 snapshots regressão",c["signal"]=="REGRESSION"),("regressão permite reação",c["enough_for_reaction"]),("reforça fundamentos",s["action"]=="REINFORCE_FOUNDATION"),("confiança moderada",c["confidence"]=="MODERATE")]
d=run([3.08,9.4,17.2]); c=d["context"]; s=d["strategy"]
cases += [("3 snapshots melhora",c["signal"]=="IMPROVEMENT"),("melhora permite reação",c["enough_for_reaction"]),("prepara avanço",s["action"]=="RECOGNIZE_AND_PREPARE_ADVANCE"),("não avança dificuldade sozinho",s["current_difficulty"]=="FOUNDATION")]
e=run([3,8,15,24]); c=e["context"]
cases += [("4 snapshots melhora",c["signal"]=="IMPROVEMENT"),("confiança alta",c["confidence"]=="HIGH"),("3 movimentos consecutivos",c["consecutive_moves"]==3)]
f=run([10,11,10.5,11]); c=f["context"]; s=f["strategy"]
cases += [("oscilação não vira melhora",c["signal"]=="STABLE_OR_MIXED"),("oscilação mantém",s["action"]=="MAINTAIN")]
cases += [("prioridade preservada",a["strategy"]["priority_skill_id"]=="leveling"),("task preservada",a["strategy"]["current_task_id"]=="plan_level_before_spending"),("difficulty preservada",a["strategy"]["current_difficulty"]=="FOUNDATION"),("safeguards presentes",len(a["strategy"]["safeguards"])==3)]

print("="*82); print("TFT INSIGHT - FASE 13.1 A 13.4 - PROGRESS-AWARE COACH V1"); print("="*82)
passed=0
for i,(name,ok) in enumerate(cases,1):
    passed+=int(ok); print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
print("\n"+"="*82); print(f"PASSARAM: {passed}/{len(cases)}")
if passed==len(cases): print("FASE 13.1-13.4 PROGRESS-AWARE COACH V1: VALIDADA"); raise SystemExit(0)
print("FASE 13.1-13.4: AJUSTE NECESSÁRIO"); raise SystemExit(1)
