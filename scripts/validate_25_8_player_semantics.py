import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from composition_v2_fixture import composition_a,composition_b
from src.decision_engine import CompositionHistoryAnalyzer
from src.composition_intelligence_v2 import CompositionIntelligenceV2
history=CompositionHistoryAnalyzer.analyze([
composition_a("A1",1),composition_a("A2",2),composition_a("A3",3),
composition_b("B1",6),composition_b("B2",7)
])
r=CompositionIntelligenceV2.build(history)
public=" ".join((r.repetition_signal,r.repetition_interpretation,*r.limitations))
checks=[
("Não prova intenção","não prova" in public.lower()),
("Explica board final","board final" in public.lower()),
("Protege pivot/transição","transições" in public.lower()),
("Protege escolha específica","lobby específico" in public.lower()),
("Não afirma deveria ter pivotado","deveria ter pivotado" not in public.lower()),
]
print("="*92);print("#25.8 - PLAYER-FACING SEMANTICS");print("="*92)
passed=sum(int(o) for _,o in checks)
for i,(n,o) in enumerate(checks,1):print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print("\\nLeitura:",r.repetition_interpretation)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed!=len(checks):raise SystemExit(1)
print("#25.8: VALIDADO")
