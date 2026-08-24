
from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from src.next_match_plan import NextMatchPlanService
from src.recommendation_guardrails import RecommendationGuardrails

@dataclass
class Recommendation:
    title: str
    recommendation: str
    why_now: str = ""
    competitive_context: str = ""
    training_context: str = ""
    preserve: str | None = None
    secondary_actions: tuple = ()

safe = Recommendation(
    title="Planeje a próxima subida antes de gastar",
    recommendation=(
        "Antes de comprar experiência, defina qual nível você quer alcançar "
        "e qual condição faria você estabilizar antes."
    ),
    preserve="Economia",
    secondary_actions=(
        "Cheque se seu board está preservando vida antes de investir pesado.",
    ),
)

safe_guardrails = RecommendationGuardrails.validate(
    recommendation=safe,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    direct_evidence_count=0,
)

plan = NextMatchPlanService.build(
    recommendation=safe,
    guardrails=safe_guardrails,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    mission_objective=(
        "Antes de gastar ouro, defina qual será seu próximo momento "
        "de subida de nível."
    ),
)

unsafe = Recommendation(
    title="Timing obrigatório",
    recommendation="Você perdeu porque deveria subir no 4-2.",
)

unsafe_guardrails = RecommendationGuardrails.validate(
    recommendation=unsafe,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    direct_evidence_count=0,
)

blocked = NextMatchPlanService.build(
    recommendation=unsafe,
    guardrails=unsafe_guardrails,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
)

checks = [
    ("Plano seguro é publicável", plan.publishable is True),
    ("Mantém Skill", plan.active_skill_label == "Leveling"),
    ("Mantém missão", plan.mission_title == "Planejar o próximo nível"),
    ("Mantém objetivo", "Antes de gastar ouro" in plan.mission_objective),
    ("Usa recomendação aprovada", "Planeje a próxima subida" in plan.primary_title),
    ("Usa ação aprovada", "Antes de comprar experiência" in plan.primary_action),
    ("Preserva Economia", plan.preserve == "Economia"),
    ("Tem no máximo 2 sinais", len(plan.watch_items) <= 2),
    ("Mantém sinal de apoio", len(plan.watch_items) == 1),
    ("Tem lembrete pedagógico", "uma decisão de cada vez" in plan.coach_reminder),
    ("Sem motivo de bloqueio", plan.blocked_reason is None),
    ("Recomendação insegura bloqueia", blocked.publishable is False),
    ("Plano bloqueado não publica ação", blocked.primary_action == ""),
    ("Expõe motivo do bloqueio", bool(blocked.blocked_reason)),
    ("Não muda prioridade", plan.changes_learning_priority is False),
    ("Não muda missão", plan.changes_mission is False),
    ("Não muda dificuldade", plan.changes_difficulty is False),
    ("Não muda EvidenceClass", plan.changes_evidence_class is False),
    ("Não conta como missão", plan.counts_as_mission_evidence is False),
    ("Não prevê rank up", plan.predicts_rank_up is False),
]

print("="*96)
print("TFT INSIGHT - NEXT MATCH PLAN V1")
print("="*96)
passed=0
for i,(name,ok) in enumerate(checks,1):
    passed += int(ok)
    print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
print("\n"+"="*96)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed == len(checks):
    print("NEXT MATCH PLAN V1: VALIDADO")
else:
    print("NEXT MATCH PLAN V1: FALHOU")
    raise SystemExit(1)
