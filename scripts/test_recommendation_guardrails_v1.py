
from __future__ import annotations
import sys
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.recommendation_guardrails import RecommendationGuardrails

@dataclass
class Recommendation:
    title:str
    recommendation:str
    why_now:str=""
    competitive_context:str=""
    training_context:str=""
    preserve:str|None=None
    secondary_actions:tuple=()

def v(rec,direct=0):
    return RecommendationGuardrails.validate(
        recommendation=rec,
        active_skill_label="Leveling",
        mission_title="Planejar o próximo nível",
        direct_evidence_count=direct,
    )

safe=Recommendation(
    "Planeje a próxima subida antes de gastar",
    "Antes de comprar experiência, defina qual nível quer alcançar e qual condição faria você estabilizar antes.",
    "Seu nível final médio vem terminando mais baixo. Isso não prova piora de decisão.",
    "Use Entrada do Avançado BR como contexto, não como requisito de promoção.",
    "O foco permanece em Leveling.",
    "Economia",
    ("Cheque se o board está preservando vida.",)
)
cause=Recommendation("x","Você perdeu porque não subiu de nível.")
timing=Recommendation("x","Você deveria subir no 4-2.")
rank=Recommendation("x","Seguindo isso você vai subir.")
mission=Recommendation("x","Você falhou na missão.")
priority=Recommendation("x","Troque seu foco de Leveling para Economia.")
many=Recommendation("x","Mantenha o foco.",secondary_actions=("A","B","C"))

rs,rc,rt,rr,rm,rp,rn = map(v,[safe,cause,timing,rank,mission,priority,many])
checks=[
("Recomendação segura passa",rs.passed),
("Segura sem bloqueios",rs.blocked_count==0),
("Causalidade falsa bloqueia",not rc.passed),
("Detecta FALSE_CAUSALITY",any(x.rule_id=="FALSE_CAUSALITY" for x in rc.findings)),
("Timing 4-2 bloqueia",not rt.passed),
("Detecta UNSUPPORTED_TIMING",any(x.rule_id=="UNSUPPORTED_TIMING" for x in rt.findings)),
("Prevê rank up bloqueia",not rr.passed),
("Detecta RANK_UP_PREDICTION",any(x.rule_id=="RANK_UP_PREDICTION" for x in rr.findings)),
("Julgar missão bloqueia",not rm.passed),
("Detecta julgamento missão",any(x.rule_id=="UNSUPPORTED_MISSION_JUDGMENT" for x in rm.findings)),
("Troca prioridade bloqueia",not rp.passed),
("Detecta troca não autorizada",any(x.rule_id=="UNAUTHORIZED_PRIORITY_CHANGE" for x in rp.findings)),
("Excesso ações gera warning",rn.warning_count>=1),
("Warning não bloqueia",rn.passed),
("Não muda prioridade",rs.changes_learning_priority is False),
("Não muda missão",rs.changes_mission is False),
("Não muda dificuldade",rs.changes_difficulty is False),
("Não muda EvidenceClass",rs.changes_evidence_class is False),
("Não conta como missão",rs.counts_as_mission_evidence is False),
("Não prevê rank up",rs.predicts_rank_up is False),
]
print("="*96)
print("TFT INSIGHT - RECOMMENDATION GUARDRAILS V1")
print("="*96)
passed=0
for i,(name,ok) in enumerate(checks,1):
    passed+=int(ok)
    print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
print("\n"+"="*96)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed==len(checks):
    print("RECOMMENDATION GUARDRAILS V1: VALIDADO")
else:
    raise SystemExit(1)
