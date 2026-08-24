import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from composition_v2_fixture import composition_a,composition_b
from src.decision_engine import CompositionHistoryAnalyzer
from src.composition_intelligence_v2 import CompositionIntelligenceV2
history=CompositionHistoryAnalyzer.analyze([
composition_a("A1",1),composition_a("A2",2),composition_a("A3",4),
composition_b("B1",6),composition_b("B2",8)
])
r=CompositionIntelligenceV2.build(history)
a=next(x for x in r.profiles if x.carry_character_id=="CarryA")
checks=[
("Média A correta",abs(a.average_placement-2.33)<0.01),
("Top4 A 100%",a.top4_rate==100.0),
("Win A > 0",a.win_rate>0),
("Usage A 60%",a.usage_rate==60.0),
("Best supported é A",r.best_supported.carry_character_id=="CarryA"),
]
print("="*92);print("#25.6 - COMPOSITION PERFORMANCE");print("="*92)
passed=sum(int(o) for _,o in checks)
for i,(n,o) in enumerate(checks,1):print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print(f"\\nPASSARAM: {passed}/{len(checks)}")
if passed!=len(checks):raise SystemExit(1)
print("#25.6: VALIDADO")
