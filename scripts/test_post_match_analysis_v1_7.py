from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = {
    "app": ROOT/"src/integration_engine/api/app.py",
    "route": ROOT/"src/integration_engine/api/routes/post_match.py",
    "client": ROOT/"partner_platform/services/api_client.py",
    "page": ROOT/"partner_platform/pages/benchmark_page.py",
    "component": ROOT/"partner_platform/components/post_match_report.py",
    "report": ROOT/"src/post_match/services/post_match_report_service.py",
}
texts={}
for name,path in files.items():
    text=path.read_text(encoding="utf-8")
    ast.parse(text)
    texts[name]=text
checks=[
("API app registra post-match","post_match_router" in texts["app"]),
("Rota latest existe",'"/player/latest"' in texts["route"]),
("Rota exige API key","Depends(require_api_key)" in texts["route"]),
("Rota usa histórico","history_size + 1" in texts["route"]),
("Rota usa cache de partidas","CachedMatchService" in texts["route"]),
("Rota usa contestação","ContestAnalyzer.analyze" in texts["route"]),
("Rota gera baseline","PersonalBaselineService.compare" in texts["route"]),
("Rota gera histórico","HistoricalMatchContextService.analyze" in texts["route"]),
("Rota gera interpretação","PostMatchInterpretationService.interpret" in texts["route"]),
("Rota gera report final","PostMatchReportService.build" in texts["route"]),
("Client possui método","def latest_post_match_report(" in texts["client"]),
("Client chama endpoint",'/v1/post-match/player/latest' in texts["client"]),
("UI possui botão","Analisar última partida" in texts["page"]),
("UI usa missão atual","_post_match_training_payload" in texts["page"]),
("UI possui cache","_post_match_cache_key" in texts["page"]),
("UI renderiza report","render_post_match_report" in texts["page"]),
("Componente mostra foco",'eyebrow="Seu foco"' in texts["component"]),
("Componente mostra próximo jogo",'eyebrow="Para o próximo jogo"' in texts["component"]),
("Detalhes técnicos recolhidos","Detalhes técnicos da análise" in texts["component"]),
("Report protege prioridade","changes_learning_priority=False" in texts["report"]),
("Report protege missão","changes_mission=False" in texts["report"]),
("Report não conta missão","counts_as_mission_evidence=False" in texts["report"]),
]
print("="*94)
print("TFT INSIGHT - POST MATCH ANALYSIS V1.7 API + UI")
print("="*94)
passed=0
for i,(name,ok) in enumerate(checks,1):
    passed+=int(ok)
    print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
print("\n"+"="*94)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed==len(checks):
    print("POST MATCH ANALYSIS V1.7: VALIDADO")
else:
    raise SystemExit(1)
