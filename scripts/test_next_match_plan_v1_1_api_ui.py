
from __future__ import annotations
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

checks=[]

def text(path):
    return (ROOT/path).read_text(encoding="utf-8")

route=text("src/integration_engine/api/routes/post_match.py")
client=text("partner_platform/services/api_client.py")
component=text("partner_platform/components/post_match_report.py")
page=text("partner_platform/pages/benchmark_page.py")

for rel in [
    "src/integration_engine/api/routes/post_match.py",
    "partner_platform/services/api_client.py",
    "partner_platform/components/post_match_report.py",
    "partner_platform/pages/benchmark_page.py",
    "src/action_signal/services/action_signal_engine.py",
    "src/contextual_recommendation/services/contextual_recommendation_engine.py",
    "src/recommendation_guardrails/services/recommendation_guardrails.py",
    "src/next_match_plan/services/next_match_plan_service.py",
]:
    try:
        ast.parse(text(rel))
        ok=True
    except Exception:
        ok=False
    checks.append((f"Syntax {rel}",ok))

checks += [
    ("API gera Action Signals","ActionSignalEngine.build(" in route),
    ("API gera Contextual Recommendation","ContextualRecommendationEngine.build(" in route),
    ("API executa Guardrails","RecommendationGuardrails.validate(" in route),
    ("API gera Next Match Plan","NextMatchPlanService.build(" in route),
    ("API expõe next_match_plan",'payload["next_match_plan"]' in route),
    ("Request recebe contexto competitivo","competitive_context: dict" in route),
    ("Request recebe Coach Fusion","coach_fusion: dict" in route),
    ("Client envia contexto competitivo",'"competitive_context": competitive_context or {}' in client),
    ("Client envia Coach Fusion",'"coach_fusion": coach_fusion or {}' in client),
    ("UI renderiza plano","_render_next_match_plan(report)" in component),
    ("UI respeita publishable",'plan.get("publishable", False)' in component),
    ("UI mostra ação principal",'eyebrow="Ação principal"' in component),
    ("UI mostra Fique de olho",'st.markdown("#### Fique de olho")' in component),
    ("UI mostra Preserve",'eyebrow="Preserve"' in component),
    ("Página passa benchmark real","benchmark_name=benchmark_name" in page),
    ("Página passa Spectrum real","spectrum=spectrum" in page),
    ("Página passa Coach Fusion",'comparison.get("coach_fusion", {})' in page),
    ("Guardrails bloqueiam publicação","publishable=False" in text("src/next_match_plan/services/next_match_plan_service.py")),
    ("Next Match Plan não troca prioridade","changes_learning_priority: bool = False" in text("src/next_match_plan/models/next_match_plan.py")),
    ("Next Match Plan não prevê rank up","predicts_rank_up: bool = False" in text("src/next_match_plan/models/next_match_plan.py")),
]

print("="*96)
print("TFT INSIGHT - NEXT MATCH PLAN V1.1 API + UI")
print("="*96)
passed=0
for i,(name,ok) in enumerate(checks,1):
    passed+=int(ok)
    print(f"\\n[{i}] {name}\\nStatus  : {'OK' if ok else 'ERRO'}")
print("\\n"+"="*96)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed==len(checks):
    print("NEXT MATCH PLAN V1.1 API + UI: VALIDADO")
else:
    print("NEXT MATCH PLAN V1.1 API + UI: FALHOU")
    raise SystemExit(1)
