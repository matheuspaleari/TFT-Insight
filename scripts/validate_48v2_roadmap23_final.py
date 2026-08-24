from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

files = {
    "home": ROOT / "partner_platform/pages/home_page.py",
    "benchmark": ROOT / "partner_platform/pages/benchmark_page.py",
    "context": ROOT / "partner_platform/platform_core/context.py",
    "router": ROOT / "partner_platform/platform_core/router.py",
    "catalog": ROOT / "partner_platform/navigation/catalog.py",
    "theme": ROOT / "partner_platform/theme/theme.py",
    "intelligence_css": ROOT / "partner_platform/assets/roadmap23_intelligence.css",
    "coach_css": ROOT / "partner_platform/assets/roadmap23_coach.css",
    "trust_css": ROOT / "partner_platform/assets/roadmap23_trust.css",
    "finish_css": ROOT / "partner_platform/assets/roadmap23_finish.css",
}

missing = [str(p) for p in files.values() if not p.exists()]
if missing:
    print("ERRO: arquivos obrigatórios ausentes:")
    for item in missing:
        print(f"- {item}")
    raise SystemExit(1)

t = {name: path.read_text(encoding="utf-8") for name, path in files.items()}
home, benchmark, context = t["home"], t["benchmark"], t["context"]
router, catalog, theme = t["router"], t["catalog"], t["theme"]
icss, ccss, tcss, fcss = t["intelligence_css"], t["coach_css"], t["trust_css"], t["finish_css"]

syntax_ok = True
for key in ("home", "benchmark", "context", "router", "catalog", "theme"):
    try:
        ast.parse(t[key], filename=str(files[key]))
    except Exception as exc:
        syntax_ok = False
        print(f"SINTAXE: {files[key]} -> {exc}")

css_names = (
    "roadmap23_home.css",
    "roadmap23_intelligence.css",
    "roadmap23_coach.css",
    "roadmap23_trust.css",
    "roadmap23_finish.css",
)
positions = [theme.find(x) for x in css_names]
css_order_ok = all(x >= 0 for x in positions) and positions == sorted(positions)

checks = (
    ("Arquivos obrigatórios presentes", not missing),
    ("Sintaxe Python válida", syntax_ok),
    ("Home registrada no router", '"Home": lambda: home_page.render(' in router),
    ("Home na navegação", 'page="Home"' in catalog and 'label="Início"' in catalog),
    ("Análise preservada", 'page="Benchmark"' in catalog and 'label="Análise"' in catalog),
    ("Configurações preservadas", 'page="Settings"' in catalog),
    ("Hero preservado", "Aprenda a pensar como um Challenger." in home),
    ("Proposta de valor preservada", "Transforme seu histórico de partidas" in home),
    ("Dois CTAs preservados", home.count("Analisar meu Riot ID") >= 2),
    ("Renderer HTML direto presente", "def _render_html(markup: str)" in home),
    ("st.html presente", 'hasattr(st, "html")' in home and "st.html(markup)" in home),
    ("Fallback HTML presente", "compact = re.sub(" in home),
    ("dedent antigo removido", "dedent(" not in home),
    ("Context congelado não é mutado", 'context.page = "Benchmark"' not in home),
    ("Dois CTAs usam destino pendente", home.count('st.session_state["_tft_navigation_target"] = "Benchmark"') == 2),
    ("Context consome destino pendente", '"_tft_navigation_target"' in context),
    ("Destino aplicado antes do radio", context.find('pending_page = st.session_state.pop(') < context.find('choice = st.sidebar.radio(')),
    ("Quatro inteligências na Home", all(x in home for x in ("COMPOSIÇÕES", "CONTESTAÇÃO", "ECONOMIA", "CARRIES + ITENS"))),
    ("Como funciona preservado", '"Como funciona"' in home),
    ("Diferencial do Coach preservado", '"O diferencial do Coach"' in home),
    ("Confiança preservada", "Confiança sem promessas exageradas" in home),
    ("Guardrail preservado", "Como interpretar as recomendações" in home),
    ("CTA final preservado", "Pronto para entender melhor suas partidas?" in home),
    ("Endpoint composição preservado", "api_client.composition_intelligence(" in benchmark),
    ("Endpoint contestação preservado", "api_client.contest_intelligence(" in benchmark),
    ("Endpoint economia preservado", "api_client.economy_intelligence(" in benchmark),
    ("Endpoint carries preservado", "api_client.carry_item_intelligence(" in benchmark),
    ("Atualizar composição presente", '"Atualizar análise de composições" if isinstance(cached, dict)' in benchmark),
    ("Atualizar contestação presente", '"Atualizar análise de contestação" if isinstance(cached, dict)' in benchmark),
    ("Atualizar economia presente", '"Atualizar análise de economia" if isinstance(cached, dict)' in benchmark),
    ("Atualizar carries presente", '"Atualizar análise de carries e itens" if isinstance(cached, dict)' in benchmark),
    ("Evidências composição preservadas", '"Ver evidências e detalhes de composições",' in benchmark),
    ("Evidências contestação preservadas", '"Ver evidências e detalhes de contestação",' in benchmark),
    ("Evidências economia preservadas", '"Ver evidências e detalhes de economia",' in benchmark),
    ("Evidências carries preservadas", '"Ver evidências e detalhes de carries + itens",' in benchmark),
    ("Expansão pós-clique presente", benchmark.count("expanded=bool(analyze)") >= 4),
    ("CSS Roadmap 23 em ordem", css_order_ok),
    ("Grid responsivo preservado", "repeat(4, minmax(0, 1fr))" in icss and "repeat(2, minmax(0, 1fr))" in icss),
    ("Coach responsivo", "@media (max-width: 900px)" in ccss),
    ("Confiança responsiva", "@media (max-width: 760px)" in tcss),
    ("Notebook coberto", "@media (max-width: 1366px)" in fcss),
    ("Tablet coberto", "@media (max-width: 900px)" in fcss),
    ("Mobile coberto", "@media (max-width: 680px)" in fcss),
    ("Textos longos protegidos", "overflow-wrap: anywhere" in fcss),
    ("Reduced motion preservado", "prefers-reduced-motion: reduce" in fcss),
)

print("=" * 112)
print("#48V2 / ROADMAP 23.9 - AUDITORIA FINAL PÓS-HOTFIXES")
print("=" * 112)
passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<78} {'OK' if ok else 'ERRO'}")
print("-" * 112)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    print("#48V2 ROADMAP 23.9: REVISAR")
    raise SystemExit(1)

print("#48V2 ROADMAP 23.9: AUDITORIA FINAL VALIDADA")
print("ROADMAP 23 - LANDING / HOME: CONCLUIDA")
print("PROXIMA ETAPA: ROADMAP 24 - GITHUB + README + ARQUITETURA")
