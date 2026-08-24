from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "README.md"
text = path.read_text(encoding="utf-8") if path.exists() else ""

checks = (
    ("README presente", path.exists()),
    ("Badge Python", "img.shields.io/badge/Python" in text),
    ("Badge FastAPI", "img.shields.io/badge/FastAPI" in text),
    ("Badge Streamlit", "img.shields.io/badge/Streamlit" in text),
    ("Card Composições", "### 🧩 Composições" in text),
    ("Card Contestação", "### ⚔️ Contestação" in text),
    ("Card Economia", "### 💰 Economia" in text),
    ("Card Carries + Itens", "### 🎯 Carries + Itens" in text),
    ("Card Evidence-first", "### 🧠 Evidence-first" in text),
    ("Card Coach", "### 🧭 Coach orientado à decisão" in text),
    ("Card Guardrails", "### 🛡️ Guardrails" in text),
    ("Seção demonstração", "## Demonstração" in text),
    ("Arquitetura preservada", "## Arquitetura" in text),
    ("Setup preservado", "## Executando localmente" in text),
)

print("="*108)
print("#52B / ROADMAP 24.5 - CARDS VISUAIS DO README")
print("="*108)
passed = 0
for i,(label,ok) in enumerate(checks,1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<78} {'OK' if ok else 'ERRO'}")
print("-"*108)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed != len(checks):
    raise SystemExit(1)
print("#52B ROADMAP 24.5: CARDS DO README VALIDADOS")
