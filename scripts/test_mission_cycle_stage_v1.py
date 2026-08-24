from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.training.services.mission_cycle_stage_resolver import MissionCycleStage, MissionCycleStageResolver

def main():
    cases=[(0,5,MissionCycleStage.START),(1,5,MissionCycleStage.EARLY),(2,5,MissionCycleStage.EARLY),(3,5,MissionCycleStage.MID),(4,5,MissionCycleStage.FINAL),(5,5,MissionCycleStage.COMPLETED)]
    checks=[]
    for c,t,e in cases:
        r=MissionCycleStageResolver.resolve(games_completed=c,games_target=t)
        checks.append((f"{c}/{t} -> {e.value}", r.stage==e and bool(r.label) and bool(r.message)))
    pp=ROOT/'src/coach/services/coach_pipeline_service.py'; rp=ROOT/'src/integration_engine/api/routes/benchmark.py'; cp=ROOT/'src/integration_engine/contracts/benchmark.py'; up=ROOT/'partner_platform/pages/benchmark_page.py'
    for p in (pp,rp,cp,up): ast.parse(p.read_text(encoding='utf-8'))
    ps=pp.read_text(encoding='utf-8'); rs=rp.read_text(encoding='utf-8'); cs=cp.read_text(encoding='utf-8'); us=up.read_text(encoding='utf-8')
    checks += [("Pipeline resolve estágio", "MissionCycleStageResolver.resolve" in ps),("API expõe cycle_stage", '"cycle_stage": pipeline.cycle_stage' in rs),("Contrato aceita cycle_message", "cycle_message: str" in cs),("UI mostra Momento do ciclo", 'eyebrow="Momento do ciclo"' in us),("UI não calcula estágio", "MissionCycleStageResolver" not in us)]
    print('='*82); print('TFT INSIGHT - MISSION CYCLE STAGE V1'); print('='*82)
    passed=0
    for i,(name,ok) in enumerate(checks,1):
        passed += int(ok); print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
    print('\n'+'='*82); print(f'PASSARAM: {passed}/{len(checks)}')
    if passed==len(checks): print('MISSION CYCLE STAGE V1: VALIDADO'); raise SystemExit(0)
    print('MISSION CYCLE STAGE V1: AJUSTE NECESSÁRIO'); raise SystemExit(1)
if __name__=='__main__': main()
