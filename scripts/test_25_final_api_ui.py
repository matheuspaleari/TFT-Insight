from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "app": ROOT / "src/integration_engine/api/app.py",
    "route": ROOT / "src/integration_engine/api/routes/composition_intelligence.py",
    "client": ROOT / "partner_platform/services/api_client.py",
    "page": ROOT / "partner_platform/pages/benchmark_page.py",
    "component": ROOT / "partner_platform/components/composition_intelligence.py",
    "presenter": ROOT / "src/composition_intelligence_v2/services/composition_player_presenter.py",
    "engine": ROOT / "src/composition_intelligence_v2/services/composition_intelligence_v2.py",
}

texts = {}

for name, path in FILES.items():
    text = path.read_text(
        encoding="utf-8"
    )
    ast.parse(
        text
    )
    texts[name] = text

checks = [
    (
        "API registra Composition router",
        "composition_intelligence_router"
        in texts["app"],
    ),
    (
        "Endpoint player/history existe",
        '"/player/history"'
        in texts["route"],
    ),
    (
        "Endpoint exige API key",
        "Depends(require_api_key)"
        in texts["route"],
    ),
    (
        "Endpoint busca candidatos extras",
        "request.match_count * 2"
        in texts["route"],
    ),
    (
        "Endpoint tolera partidas inválidas",
        "load_result.failed_matches"
        in texts["route"],
    ),
    (
        "Usa Contest History",
        "ContestHistoryAnalyzer.analyze"
        in texts["route"],
    ),
    (
        "Usa Composition History",
        "CompositionHistoryAnalyzer.analyze"
        in texts["route"],
    ),
    (
        "Usa Composition Intelligence V2",
        "CompositionIntelligenceV2.build"
        in texts["route"],
    ),
    (
        "Usa Presenter público",
        "CompositionPlayerPresenter.build"
        in texts["route"],
    ),
    (
        "Client possui composition_intelligence",
        "def composition_intelligence("
        in texts["client"],
    ),
    (
        "Client chama endpoint correto",
        "/v1/composition-intelligence/player/history"
        in texts["client"],
    ),
    (
        "Página possui botão",
        "Analisar composições"
        in texts["page"],
    ),
    (
        "Página usa cache",
        "_composition_intelligence_cache_key"
        in texts["page"],
    ),
    (
        "Página renderiza componente",
        "render_composition_intelligence"
        in texts["page"],
    ),
    (
        "UI mostra resumo",
        '"Composições"'
        in texts["component"],
    ),
    (
        "UI mostra mais usada",
        'eyebrow="Mais usada"'
        in texts["component"],
    ),
    (
        "UI mostra melhor com amostra",
        "Melhor resultado com amostra mínima"
        in texts["component"],
    ),
    (
        "UI separa confiança",
        "statistical_confidence"
        in texts["component"],
    ),
    (
        "Support não está na UI pública",
        "support_character_id"
        not in texts["component"],
    ),
    (
        "Presenter não expõe Support",
        '"support_character_id"'
        not in texts["presenter"],
    ),
    (
        "Presenter usa eligible_for_comparison",
        "eligible_for_comparison"
        in texts["presenter"],
    ),
    (
        "Guardrail força/intenção",
        "não prova intenção"
        in texts["presenter"],
    ),
]

print("=" * 100)
print(
    "TFT INSIGHT - #25 FINAL API + UI"
)
print("=" * 100)

passed = 0

for index, (
    name,
    ok,
) in enumerate(
    checks,
    1,
):
    passed += int(
        ok
    )

    print()
    print(
        f"[{index}] {name}"
    )
    print(
        f"Status  : "
        f"{'OK' if ok else 'ERRO'}"
    )

print()
print("=" * 100)
print(
    f"PASSARAM: "
    f"{passed}/{len(checks)}"
)

if passed == len(
    checks
):
    print(
        "#25 FINAL API + UI: VALIDADO"
    )
else:
    print(
        "#25 FINAL API + UI: FALHOU"
    )
    raise SystemExit(1)
