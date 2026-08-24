from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

paths = {
    "engine": ROOT / "src/carry_item_intelligence/services/carry_item_intelligence_engine.py",
    "presenter": ROOT / "src/carry_item_intelligence/services/carry_item_player_presenter.py",
    "route": ROOT / "src/integration_engine/api/routes/carry_item_intelligence.py",
    "app": ROOT / "src/integration_engine/api/app.py",
    "client": ROOT / "partner_platform/services/api_client.py",
    "page": ROOT / "partner_platform/pages/benchmark_page.py",
    "ui": ROOT / "partner_platform/components/carry_item_intelligence.py",
}

texts = {}
for name, path in paths.items():
    text = path.read_text(encoding="utf-8")
    ast.parse(text)
    texts[name] = text

checks = [
    ("Engine existe", "class CarryItemIntelligenceEngine" in texts["engine"]),
    ("Usa ItemizationHistoryAnalyzer", "ItemizationHistoryAnalyzer.analyze" in texts["engine"]),
    ("Usa RoleInferenceEngine", "RoleInferenceEngine.infer_participant" in texts["engine"]),
    ("Amostra mínima 3", "MIN_SAMPLE = 3" in texts["engine"]),
    ("Agrupa por carry", "by_carry" in texts["engine"]),
    ("Agrupa builds", "build_groups" in texts["engine"]),
    ("Itens recorrentes", "most_used_items" in texts["engine"]),
    ("Melhor carry elegível", "best_supported" in texts["engine"]),
    ("Não inventa timing", "não informa em qual round" in texts["engine"]),
    ("Não afirma causalidade", "não prova que os itens causaram" in texts["engine"]),
    ("Presenter existe", "class CarryItemPlayerPresenter" in texts["presenter"]),
    ("Coach protege escolha universal", "não significa que seja a melhor escolha" in texts["presenter"]),
    ("Endpoint existe", "/v1/carry-item-intelligence" in texts["route"]),
    ("Usa ItemClassificationProvider", "ItemClassificationProvider" in texts["route"]),
    ("Usa CachedMatchService", "CachedMatchService" in texts["route"]),
    ("Router registrado", "carry_item_intelligence_router" in texts["app"]),
    ("Client integrado", "def carry_item_intelligence(" in texts["client"]),
    ("UI existe", "render_carry_item_intelligence" in texts["ui"]),
    ("UI carry mais usado", '"Seu carry mais recorrente"' in texts["ui"]),
    ("UI itens recorrentes", '"Itens mais recorrentes"' in texts["ui"]),
    ("UI builds", '"Builds observadas"' in texts["ui"]),
    ("UI última partida", '"Última partida"' in texts["ui"]),
    ("UI melhor elegível", '"Melhor histórico com amostra mínima"' in texts["ui"]),
    ("UI guardrails", '"Como interpretar esta análise"' in texts["ui"]),
    ("Página botão", "Analisar carries e itens" in texts["page"]),
    ("Página renderiza", "_render_carry_item_intelligence_integration" in texts["page"]),
    ("Não altera prioridade", "changes_learning_priority" not in texts["engine"]),
    ("Não altera missão", "changes_mission" not in texts["engine"]),
    ("Não prevê rank up", "predicts_rank_up" not in texts["engine"]),
]

print("=" * 100)
print("TFT INSIGHT - #28 ITENS + CARRIES")
print("=" * 100)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{i}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#28 ITENS + CARRIES: CONTRATO VALIDADO")
else:
    raise SystemExit(1)
