
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from src.contextual_recommendation import ContextualRecommendationEngine
from src.recommendation_guardrails import RecommendationGuardrails

class FakeAction:
    def __init__(self,title,action,reason):
        self.title=title;self.action=action;self.reason=reason

class FakeActions:
    def __init__(self):
        self.primary=FakeAction(
            "Planeje a próxima subida antes de gastar",
            "Antes de comprar experiência, defina qual nível você quer alcançar e qual condição faria você estabilizar antes.",
            "Seu nível final médio vem terminando mais baixo no bloco recente. Isso não prova piora de decisão."
        )
        self.secondary=(FakeAction(
            "Cheque pressão",
            "Compare se seu board está preservando vida e convertendo força em pressão.",
            "Pressão abaixo do padrão."
        ),)

actions=FakeActions()
recommendation=ContextualRecommendationEngine.build(
    action_signals=actions,
    competitive_context={"group_label":"Avançado BR","spectrum_band":"Entrada"},
    coach_fusion={
        "problem_observed":"Leveling é a principal oportunidade de treino",
        "training_focus":"Planejar o próximo nível",
        "strength_to_preserve":"Economia",
    },
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
)
guardrails=RecommendationGuardrails.validate(
    recommendation=recommendation,
    action_signals=actions,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    direct_evidence_count=0,
)

print("="*96)
print("RECOMMENDATION GUARDRAILS V1")
print("="*96)
print("\nRECOMENDAÇÃO VALIDADA\n"+"-"*96)
print(recommendation.title)
print(recommendation.recommendation)
print("\nRESULTADO DOS GUARDRAILS\n"+"-"*96)
print(f"Passed        : {guardrails.passed}")
print(f"Bloqueios     : {guardrails.blocked_count}")
print(f"Warnings      : {guardrails.warning_count}")
print(f"Infos         : {guardrails.info_count}")
if guardrails.findings:
    print("\nACHADOS\n"+"-"*96)
    for item in guardrails.findings:
        print(f"[{item.severity.value}] {item.rule_id}")
        print(item.message)
        if item.field: print(f"Campo: {item.field}")
        if item.excerpt: print(f"Trecho: {item.excerpt}")
        print()
else:
    print("\nNenhum problema encontrado.")
print("\nPROTEÇÕES\n"+"-"*96)
print(f"changes_learning_priority : {guardrails.changes_learning_priority}")
print(f"changes_mission           : {guardrails.changes_mission}")
print(f"changes_difficulty        : {guardrails.changes_difficulty}")
print(f"changes_evidence_class    : {guardrails.changes_evidence_class}")
print(f"counts_as_mission_evidence: {guardrails.counts_as_mission_evidence}")
print(f"predicts_rank_up          : {guardrails.predicts_rank_up}")
print("\n"+"="*96)
print("DIAGNÓSTICO CONCLUÍDO")
print("Envie desde 'RECOMMENDATION GUARDRAILS V1' até o final.")
print("="*96)
