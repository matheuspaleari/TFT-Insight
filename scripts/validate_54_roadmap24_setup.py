from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/SETUP.md"
text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""

required_files = (
    ROOT / "run_api.py",
    ROOT / "requirements.txt",
    ROOT / "scripts/run_partner_platform.py",
    ROOT / "partner_platform/app.py",
    ROOT / "scripts/validate_51_roadmap24_official_suite.py",
)

required_content = (
    "# Setup e execução do TFT Insight",
    "RIOT_API_KEY=",
    "python run_api.py",
    r"python scripts\run_partner_platform.py",
    "http://127.0.0.1:8000",
    "TFT_INSIGHT_LOCAL_AI_ENABLED=false",
    "TFT_INSIGHT_LOCAL_AI_MODEL=llama3.2:3b",
    "TFT_INSIGHT_OLLAMA_URL=http://localhost:11434",
    "TFT_INSIGHT_LOCAL_AI_TIMEOUT=45",
    "--profile quick",
    "--profile full --guardrails",
    "## 13. Smoke test manual",
    "## 14. Troubleshooting",
    "## 15. O que não publicar",
)

forbidden = (
    "app/streamlit_app.py",
    "partner_dashboard/app.py",
)

checks: list[tuple[str, bool]] = [
    ("docs/SETUP.md presente", DOC.exists()),
    ("Guia possui conteúdo", len(text.strip()) > 5000),
]

checks.extend(
    (
        f"Arquivo real presente: {path.relative_to(ROOT)}",
        path.exists(),
    )
    for path in required_files
)

checks.extend(
    (
        f"Setup documenta: {item}",
        item in text,
    )
    for item in required_content
)

checks.extend(
    (
        f"Entrypoint legado ausente: {item}",
        item not in text,
    )
    for item in forbidden
)

# Segurança documental: exemplos nunca devem conter uma chave Riot com formato
# plausível preenchido. O guia deve usar placeholder.
for line in text.splitlines():
    stripped = line.strip()
    if stripped.startswith("RIOT_API_KEY="):
        value = stripped.split("=", 1)[1].strip()
        safe = value in {
            "sua_chave_aqui",
            "...",
            "",
        }
        checks.append(
            ("Exemplo RIOT_API_KEY não contém segredo", safe)
        )
        break
else:
    checks.append(
        ("Exemplo RIOT_API_KEY não contém segredo", False)
    )

print("=" * 114)
print("#54 / ROADMAP 24.7 - SETUP E EXECUÇÃO")
print("=" * 114)

passed = 0

for index, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(
        f"[{index:02d}] "
        f"{label:<84} "
        f"{'OK' if ok else 'ERRO'}"
    )

print("-" * 114)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    print("#54 ROADMAP 24.7: REVISAR")
    raise SystemExit(1)

print("#54 ROADMAP 24.7: SETUP DOCUMENTADO E VALIDADO")
