from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

paths = {
    "engine": ROOT / "src/economy_intelligence/services/economy_intelligence_engine.py",
    "presenter": ROOT / "src/economy_intelligence/services/economy_player_presenter.py",
    "route": ROOT / "src/integration_engine/api/routes/economy_intelligence.py",
    "app": ROOT / "src/integration_engine/api/app.py",
    "client": ROOT / "partner_platform/services/api_client.py",
    "page": ROOT / "partner_platform/pages/benchmark_page.py",
    "ui": ROOT / "partner_platform/components/economy_intelligence.py",
}

texts = {}
for name, path in paths.items():
    text = path.read_text(encoding="utf-8")
    ast.parse(text)
    texts[name] = text

checks = [
    ("Engine existe", "class EconomyIntelligenceEngine" in texts["engine"]),
    ("Reutiliza EconomyReport", "EconomyReport" in texts["engine"]),
    ("Mínimo 3 por grupo", "MIN_GROUP_SAMPLE = 3" in texts["engine"]),
    ("Trend usa blocos", "TREND_BLOCK_SIZE = 10" in texts["engine"]),
    ("Distribui ouro final", "gold_20_plus" in texts["engine"]),
    ("Distribui níveis", "level_9_plus" in texts["engine"]),
    ("Compara nível 9", "_placement_comparison" in texts["engine"]),
    ("Não inventa timing XP", "timing de compra de experiência" in texts["engine"]),
    ("Não inventa roll", "cada roll" in texts["engine"]),
    ("Não julga ouro isoladamente", "muito ou pouco ouro foi correto ou incorreto" in texts["engine"]),
    ("Presenter existe", "class EconomyPlayerPresenter" in texts["presenter"]),
    ("Coach protege Fast 9", "não uma recomendação automática de Fast 9" in texts["presenter"]),
    ("Endpoint existe", "/v1/economy-intelligence" in texts["route"]),
    ("Endpoint usa EconomyHistoryAnalyzer", "EconomyHistoryAnalyzer.analyze" in texts["route"]),
    ("Endpoint usa cache", "CachedMatchService" in texts["route"]),
    ("Router registrado", "economy_intelligence_router" in texts["app"]),
    ("Client integrado", "def economy_intelligence(" in texts["client"]),
    ("UI existe", "render_economy_intelligence" in texts["ui"]),
    ("UI mostra nível médio", '"Nível médio"' in texts["ui"]),
    ("UI mostra ouro restante", '"Ouro restante"' in texts["ui"]),
    ("UI mostra estados finais", '"Estados finais recorrentes"' in texts["ui"]),
    ("UI mostra histórico recente", '"Histórico recente"' in texts["ui"]),
    ("UI compara nível 9", '"Nível 9+ e resultado"' in texts["ui"]),
    ("UI expõe limitações", '"O que ainda não conseguimos medir"' in texts["ui"]),
    ("Página possui botão", "Analisar economia" in texts["page"]),
    ("Página renderiza módulo", "_render_economy_intelligence_integration" in texts["page"]),
    ("Não altera Learning Priority", "changes_learning_priority" not in texts["engine"]),
    ("Não altera missão", "changes_mission" not in texts["engine"]),
    ("Não prevê rank up", "predicts_rank_up" not in texts["engine"]),
]

print("=" * 100)
print("TFT INSIGHT - #27 ECONOMIA AVANÇADA")
print("=" * 100)

passed = 0
for index, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{index}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#27 ECONOMIA AVANÇADA: CONTRATO VALIDADO")
else:
    raise SystemExit(1)
