from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
doc = ROOT / "docs/ARCHITECTURE.md"
text = doc.read_text(encoding="utf-8") if doc.exists() else ""

required = (
    "# Arquitetura do TFT Insight",
    "## Visão geral",
    "## Fluxo principal de coaching",
    "Player Analysis",
    "Skill Mapping",
    "Inspector",
    "Coach Context",
    "Habits",
    "Skill Signals",
    "Evidence Fusion",
    "Learning Priority",
    "Training Plan",
    "Training Mission",
    "Coach Report",
    "## Partner Platform",
    "## API e integração",
    "## Determinístico vs. narrativa local",
    "LocalCoachNarrator",
    "## Cache",
    "## Contratos e compatibilidade",
    "LearningRecommendation",
    "## Guardrails arquiteturais",
    "IA narra; Engine decide",
    "## Validação da arquitetura",
    "validate_51_roadmap24_official_suite.py --profile full --guardrails",
)

checks = [
    ("ARCHITECTURE.md presente", doc.exists()),
    ("Documento possui conteúdo", len(text.strip()) > 5000),
    ("Mermaid presente", text.count("```mermaid") >= 3),
]

checks.extend(
    (f"Contrato documentado: {item}", item in text)
    for item in required
)

for forbidden in (
    "app/streamlit_app.py",
    "partner_dashboard/app.py",
):
    checks.append(
        (f"Entrypoint legado não é arquitetura atual: {forbidden}", forbidden not in text)
    )

print("=" * 112)
print("#53 / ROADMAP 24.6 - ARQUITETURA ATUAL")
print("=" * 112)

passed = 0
for index, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{index:02d}] {label:<82} {'OK' if ok else 'ERRO'}")

print("-" * 112)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    print("#53 ROADMAP 24.6: REVISAR")
    raise SystemExit(1)

print("#53 ROADMAP 24.6: ARQUITETURA DOCUMENTADA E VALIDADA")
