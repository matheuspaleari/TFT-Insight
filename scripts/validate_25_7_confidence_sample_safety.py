import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from composition_v2_fixture import composition_a,composition_b
from src.decision_engine import CompositionHistoryAnalyzer
from src.composition_intelligence_v2 import CompositionIntelligenceV2
history=CompositionHistoryAnalyzer.analyze([
composition_a("A1",1),composition_a("A2",2),composition_a("A3",3),
composition_b("B1",1)
])
r=CompositionIntelligenceV2.build(history)
a=next(x for x in r.profiles if x.carry_character_id=="CarryA")
b=next(x for x in r.profiles if x.carry_character_id=="CarryB")
checks=[
("3 partidas confiável",a.sample_is_reliable is True),
("1 partida não confiável",b.sample_is_reliable is False),
("Confiança A > B",a.confidence_score>b.confidence_score),
("B exploratória",b.confidence_level=="Exploratória"),
("Melhor suportada ignora lucky 1-game",r.best_supported.carry_character_id=="CarryA"),
]
print("="*92);print("#25.7 - CONFIDENCE + SAMPLE SAFETY");print("="*92)
passed=sum(int(o) for _,o in checks)
for i,(n,o) in enumerate(checks,1):print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print(f"\\nA confiança: {a.confidence_score}% ({a.confidence_level})")
print(f"B confiança: {b.confidence_score}% ({b.confidence_level})")
print(f"PASSARAM: {passed}/{len(checks)}")
if passed!=len(checks):raise SystemExit(1)
print("#25.7: VALIDADO")
