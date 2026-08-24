
from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from src.recommendation_guardrails import RecommendationGuardrails
from src.next_match_plan import NextMatchPlanService

@dataclass
class Recommendation:
    title: str
    recommendation: str
    why_now: str = ""
    competitive_context: str = ""
    training_context: str = ""
    preserve: str | None = None
    secondary_actions: tuple = ()

recommendation = Recommendation(
    title="Planeje a próxima subida antes de gastar",
    recommendation=(
        "Antes de comprar experiência, defina qual nível você quer alcançar "
        "e qual condição faria você estabilizar antes."
    ),
    why_now=(
        "Seu nível final médio vem terminando mais baixo no bloco recente. "
        "Isso não prova piora de decisão."
    ),
    competitive_context=(
        "Você está na faixa Entrada do grupo Avançado BR. "
        "Esse sinal é contexto, não requisito de promoção."
    ),
    training_context=(
        "O foco pedagógico permanece em Leveling e a missão continua sendo "
        "Planejar o próximo nível."
    ),
    preserve="Economia",
    secondary_actions=(
        "Cheque se seu board está preservando vida antes de investir pesado.",
    ),
)

guardrails = RecommendationGuardrails.validate(
    recommendation=recommendation,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    direct_evidence_count=0,
)

plan = NextMatchPlanService.build(
    recommendation=recommendation,
    guardrails=guardrails,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    mission_objective=(
        "Antes de gastar ouro, defina qual será seu próximo momento "
        "de subida de nível."
    ),
)

print("="*96)
print("NEXT MATCH PLAN V1")
print("="*96)
print("Jogador              : pinador doss#000")
print("Skill em foco        :", plan.active_skill_label)
print("Missão               :", plan.mission_title)
print("Publicável           :", plan.publishable)

if not plan.publishable:
    print("\nBLOQUEADO PELOS GUARDRAILS")
    print("-"*96)
    print(plan.blocked_reason)
else:
    print("\nPLANO PARA A PRÓXIMA PARTIDA")
    print("-"*96)
    print("\nFOCO")
    print(plan.active_skill_label)
    print("\nMISSÃO")
    print(plan.mission_title)
    if plan.mission_objective:
        print(plan.mission_objective)
    print("\nAÇÃO PRINCIPAL")
    print(plan.primary_title)
    print(plan.primary_action)
    print("\nFIQUE DE OLHO")
    if plan.watch_items:
        for item in plan.watch_items:
            print("-", item)
    else:
        print("- Nenhum sinal secundário necessário.")
    print("\nPRESERVE")
    print(plan.preserve or "-")
    print("\nLEMBRETE DO COACH")
    print(plan.coach_reminder)

print("\nPROTEÇÕES")
print("-"*96)
print(f"changes_learning_priority : {plan.changes_learning_priority}")
print(f"changes_mission           : {plan.changes_mission}")
print(f"changes_difficulty        : {plan.changes_difficulty}")
print(f"changes_evidence_class    : {plan.changes_evidence_class}")
print(f"counts_as_mission_evidence: {plan.counts_as_mission_evidence}")
print(f"predicts_rank_up          : {plan.predicts_rank_up}")
print("\n"+"="*96)
print("DIAGNÓSTICO CONCLUÍDO")
print("Envie desde 'NEXT MATCH PLAN V1' até o final.")
print("="*96)
