from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
readme = ROOT / "README.md"

required = (
    "# TFT Insight",
    "## Sobre o projeto",
    "## O que o TFT Insight analisa",
    "## Arquitetura",
    "## Stack",
    "## Executando localmente",
    "## Validação do projeto",
    "## Guardrails",
    "## Estado atual",
    "## Autor",
    "python run_api.py",
    "python scripts\\run_partner_platform.py",
    "validate_51_roadmap24_official_suite.py --profile quick",
    "validate_51_roadmap24_official_suite.py --profile full",
)

text = readme.read_text(encoding="utf-8") if readme.exists() else ""

checks = [
    ("README presente", readme.exists()),
    ("README não está vazio", len(text.strip()) > 1000),
]

checks.extend(
    (f"Conteúdo: {item}", item in text)
    for item in required
)

for forbidden in (
    "app/streamlit_app.py",
    "partner_dashboard/",
):
    checks.append(
        (f"Entrypoint legado ausente: {forbidden}", forbidden not in text)
    )

print("=" * 108)
print("#52 / ROADMAP 24.5 - README PROFISSIONAL")
print("=" * 108)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<78} {'OK' if ok else 'ERRO'}")

print("-" * 108)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    print("#52 ROADMAP 24.5: REVISAR")
    raise SystemExit(1)

print("#52 ROADMAP 24.5: README VALIDADO")
