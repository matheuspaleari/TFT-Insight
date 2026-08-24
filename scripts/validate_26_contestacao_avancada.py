from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

paths = {
    "engine": ROOT / "src/contest_intelligence/services/contest_intelligence_engine.py",
    "presenter": ROOT / "src/contest_intelligence/services/contest_player_presenter.py",
    "route": ROOT / "src/integration_engine/api/routes/contest_intelligence.py",
    "app": ROOT / "src/integration_engine/api/app.py",
    "client": ROOT / "partner_platform/services/api_client.py",
    "page": ROOT / "partner_platform/pages/benchmark_page.py",
    "ui": ROOT / "partner_platform/components/contest_intelligence.py",
}
texts = {}
for name, path in paths.items():
    text = path.read_text(encoding="utf-8")
    ast.parse(text)
    texts[name] = text

checks = [
    ("Engine existe", "class ContestIntelligenceEngine" in texts["engine"]),
    ("Reutiliza ContestHistoryReport", "ContestHistoryReport" in texts["engine"]),
    ("Amostra mínima 3/3", "MIN_GROUP_SAMPLE = 3" in texts["engine"]),
    ("Unidades recorrentes", "most_contested_units" in texts["engine"]),
    ("Traits recorrentes", "most_contested_traits" in texts["engine"]),
    ("Bandas de contestação", "ContestBandDistribution" in texts["engine"]),
    ("Não afirma scout", "não sabe se o jogador fez scout" in texts["engine"]),
    ("Não afirma causalidade", "não prova causalidade" in texts["engine"]),
    ("Presenter existe", "class ContestPlayerPresenter" in texts["presenter"]),
    ("Coach usa Contestação", "contestação" in texts["presenter"].lower()),
    ("Endpoint existe", "/v1/contest-intelligence" in texts["route"]),
    ("Endpoint usa CachedMatchService", "CachedMatchService" in texts["route"]),
    ("Router registrado", "contest_intelligence_router" in texts["app"]),
    ("Client integrado", "def contest_intelligence(" in texts["client"]),
    ("UI existe", "render_contest_intelligence" in texts["ui"]),
    ("UI carry contestado", '"Carry contestado"' in texts["ui"]),
    ("UI pressões recorrentes", '"Pressões recorrentes"' in texts["ui"]),
    ("UI protege causalidade", "não prova que a contestação causou" in texts["ui"]),
    ("Página tem botão", "Analisar contestação" in texts["page"]),
    ("Página renderiza módulo", "_render_contest_intelligence_integration" in texts["page"]),
    ("Termo público é Contestação", '"Contestação"' in texts["ui"]),
    ("Sem label público Contest", '"Contest"' not in texts["ui"]),
    ("Não altera Learning Priority", "changes_learning_priority" not in texts["engine"]),
    ("Não prevê rank up", "predicts_rank_up" not in texts["engine"]),
]

print("=" * 100)
print("TFT INSIGHT - #26 CONTESTAÇÃO AVANÇADA")
print("=" * 100)
passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")

print("\n" + "=" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed == len(checks):
    print("#26 CONTESTAÇÃO AVANÇADA: CONTRATO VALIDADO")
else:
    raise SystemExit(1)
