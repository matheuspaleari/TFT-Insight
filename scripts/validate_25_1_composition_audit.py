from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/"src"

required=[
"decision_engine/analyzers/composition_analyzer.py",
"decision_engine/analyzers/composition_identity_analyzer.py",
"decision_engine/analyzers/composition_similarity_analyzer.py",
"decision_engine/analyzers/composition_cluster_analyzer.py",
"decision_engine/analyzers/composition_history_analyzer.py",
"decision_engine/models/composition_snapshot.py",
"decision_engine/models/composition_profile.py",
"decision_engine/models/composition_history_report.py",
"coaching_engine/composition.py",
]
checks=[(path,(source/path).exists()) for path in required]
history=(source/"decision_engine/models/composition_history_report.py").read_text(encoding="utf-8")
checks += [
("forces_composition está documentado como heurística","não uma prova de intenção" in history),
("V2 existe",(source/"composition_intelligence_v2/services/composition_intelligence_v2.py").exists()),
]
print("="*92);print("#25.1 - AUDITORIA DO COMPOSITION ENGINE");print("="*92)
passed=0
for i,(n,o) in enumerate(checks,1):
    passed+=int(o);print(f"\\n[{i}] {n}\\nStatus  : {'OK' if o else 'ERRO'}")
print(f"\\nPASSARAM: {passed}/{len(checks)}")
if passed!=len(checks): raise SystemExit(1)
print("#25.1: VALIDADO")
