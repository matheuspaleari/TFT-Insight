import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from composition_v2_fixture import composition_a
from src.decision_engine.analyzers.composition_identity_analyzer import CompositionIdentityAnalyzer
m=composition_a("A1",2); p=m.analyzed_participant
r=CompositionIdentityAnalyzer.analyze(p)
checks=[
("Carry identificado",r.carry_character_id=="CarryA"),
("Traits relevantes presentes","TraitA" in r.primary_trait_names),
("Trait de role ignorada","TFT17_HPTank" not in r.primary_trait_names),
("Core limitado",len(r.core_unit_ids)<=5),
("Identity key existe",bool(r.identity_key)),
]
print("="*92);print("#25.2 - COMPOSITION IDENTITY V2");print("="*92)
passed=sum(int(o) for _,o in checks)
for i,(n,o) in enumerate(checks,1):print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print(f"\\nPASSARAM: {passed}/{len(checks)}")
if passed!=len(checks):raise SystemExit(1)
print("#25.2: VALIDADO")
