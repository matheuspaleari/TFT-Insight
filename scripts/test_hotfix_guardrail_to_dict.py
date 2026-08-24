
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.recommendation_guardrails import RecommendationGuardrails

class Recommendation:
    title = "Planeje a próxima subida antes de gastar"
    recommendation = "Antes de comprar experiência, defina qual nível você quer alcançar."
    why_now = "Isso não prova piora de decisão."
    competitive_context = ""
    training_context = ""
    preserve = "Economia"
    secondary_actions = ()

report = RecommendationGuardrails.validate(
    recommendation=Recommendation(),
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    direct_evidence_count=0,
)

payload = report.to_dict()

checks = [
    ("GuardrailReport possui to_dict", hasattr(report, "to_dict")),
    ("to_dict retorna dict", isinstance(payload, dict)),
    ("Passed serializado", payload.get("passed") is True),
    ("Findings serializado", isinstance(payload.get("findings"), list)),
    ("Blocked count serializado", payload.get("blocked_count") == 0),
    ("Proteção prioridade preservada", payload.get("changes_learning_priority") is False),
    ("Proteção missão preservada", payload.get("changes_mission") is False),
    ("Proteção dificuldade preservada", payload.get("changes_difficulty") is False),
    ("Proteção EvidenceClass preservada", payload.get("changes_evidence_class") is False),
    ("Proteção missão evidence preservada", payload.get("counts_as_mission_evidence") is False),
    ("Proteção rank up preservada", payload.get("predicts_rank_up") is False),
]

print("=" * 96)
print("TFT INSIGHT - HOTFIX GUARDRAIL REPORT TO_DICT")
print("=" * 96)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"\\n[{i}] {name}\\nStatus  : {'OK' if ok else 'ERRO'}")

print("\\n" + "=" * 96)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("HOTFIX GUARDRAIL REPORT TO_DICT: VALIDADO")
else:
    print("HOTFIX GUARDRAIL REPORT TO_DICT: FALHOU")
    raise SystemExit(1)
