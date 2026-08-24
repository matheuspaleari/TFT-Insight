from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    app = read("partner_platform/app.py")
    catalog = read("partner_platform/navigation/catalog.py")
    context = read("partner_platform/platform_core/context.py")
    benchmark = read("partner_platform/pages/benchmark_page.py")
    brand = read("partner_platform/components/sidebar_brand.py")
    session = read("partner_platform/components/current_session.py")

    for source in (app, catalog, context, benchmark, brand, session):
        ast.parse(source)

    checks = [
        ("menu automático Streamlit oculto", 'stSidebarNav' in app),
        ("Overview removida da navegação pública", 'page="Overview"' not in catalog),
        ("Playground removido da navegação pública", 'page="Playground"' not in catalog),
        ("Prediction removida da navegação pública", 'page="Prediction"' not in catalog),
        ("Developer removido da navegação pública", 'page="Developer"' not in catalog),
        ("Análise é rota principal", 'label="Análise"' in catalog and 'page="Benchmark"' in catalog),
        ("Configurações permanece", 'label="Configurações"' in catalog),
        ("fallback abre Análise", 'return "Benchmark"' in catalog),
        ("sidebar usa navegação enxuta", 'labels_for("Principal")' in context),
        ("configuração técnica fica recolhida", 'Configuração técnica' in context),
        ("status API migrou para sidebar", 'API online' in app),
        ("brand não expõe Partner Platform", 'Partner Platform' not in brand),
        ("sessão fala linguagem de jogador", 'JOGADOR ATUAL' in session),
        ("análise usa sessão persistente", 'PlayerSessionStore' in benchmark),
        ("análise chama analyze_player", 'api_client.analyze_player' in benchmark),
        ("benchmark vem do analysis report", '_analysis_benchmark_id' in benchmark),
        ("comparação usa benchmark automático", 'benchmark_id=benchmark_id' in benchmark),
        ("resultado salva análise", 'PlayerSessionStore.save_analysis' in benchmark),
        ("resultado salva benchmark", 'PlayerSessionStore.save_benchmark' in benchmark),
        ("formulário recomenda 30 partidas", 'fallback_matches=30' in benchmark),
        ("coach virou diálogo", '@st.dialog("◇ Seu Coach"' in benchmark),
        ("cristal oficial é usado", 'assets" / "crystal.png' in benchmark),
        ("cristal é flutuante", 'position: fixed' in benchmark),
        ("missão está no popup", '_render_training_mission' in benchmark),
        ("adaptive coach está no popup", '_render_adaptive_coach' in benchmark),
        ("progress-aware está no popup", '_render_progress_aware_coach' in benchmark),
        ("histórico está no popup", '_render_training_history' in benchmark),
        ("main page chama apenas cristal para coach", '_render_floating_coach' in benchmark),
    ]

    print("=" * 82)
    print("TFT INSIGHT - PRE-PRODUÇÃO P1.1 A P1.4 - UX REWORK V1")
    print("=" * 82)
    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
    print("\n" + "=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed == len(checks):
        print("P1.1-P1.4 UX REWORK V1: VALIDADA")
        raise SystemExit(0)
    print("P1.1-P1.4 UX REWORK V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
