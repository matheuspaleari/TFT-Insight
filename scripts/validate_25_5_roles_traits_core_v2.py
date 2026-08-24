import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from composition_v2_fixture import composition_a
from src.decision_engine import CompositionHistoryAnalyzer
from src.composition_intelligence_v2 import CompositionIntelligenceV2
history=CompositionHistoryAnalyzer.analyze([composition_a("A1",1),composition_a("A2",2),composition_a("A3",3)])
r=CompositionIntelligenceV2.build(history).most_used
checks=[
("Carry preservado",r.carry_character_id=="CarryA"),
("Traits expostos","TraitA" in r.primary_trait_names),
("Core units expostas","CarryA" in r.core_unit_ids),
("Máximo 5 core units",len(r.core_unit_ids)<=5),
("IDs internos permanecem dados, não nomes inventados",all(bool(x) for x in r.core_unit_ids)),
]
print("="*92);print("#25.5 - CARRY / CORE UNITS / TRAITS");print("="*92)
passed=sum(int(o) for _,o in checks)
for i,(n,o) in enumerate(checks,1):print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print(f"\\nPASSARAM: {passed}/{len(checks)}")
if passed!=len(checks):raise SystemExit(1)
print("#25.5: VALIDADO")
