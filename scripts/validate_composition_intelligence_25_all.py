from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
names=[
"validate_25_1_composition_audit.py",
"validate_25_2_identity_v2.py",
"validate_25_3_similarity_clustering_v2.py",
"validate_25_4_player_profile_v2.py",
"validate_25_5_roles_traits_core_v2.py",
"validate_25_6_performance_v2.py",
"validate_25_7_confidence_sample_safety.py",
"validate_25_8_player_semantics.py",
]
print("="*100)
print("TFT INSIGHT - #25 COMPOSITION INTELLIGENCE V2 - MASTER VALIDATION")
print("="*100)
passed=0
for name in names:
    print("\\n>>>",name)
    result=subprocess.run([sys.executable,str(ROOT/"scripts"/name)])
    if result.returncode==0:
        passed+=1
    else:
        print("\\nPARANDO NO PRIMEIRO ERRO.")
        raise SystemExit(result.returncode)
print("\\n"+"="*100)
print(f"ETAPAS VALIDADAS: {passed}/{len(names)}")
print("#25.1 → #25.8: VALIDADO")
