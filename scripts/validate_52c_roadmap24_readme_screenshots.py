from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
readme = ROOT / "README.md"
home = ROOT / "assets/readme/home.png"
analysis = ROOT / "assets/readme/analysis.png"

text = readme.read_text(encoding="utf-8") if readme.exists() else ""

checks = (
    ("README presente", readme.exists()),
    ("Screenshot Home presente", home.exists() and home.stat().st_size > 0),
    ("Screenshot Análise presente", analysis.exists() and analysis.stat().st_size > 0),
    ("README referencia Home", 'src="assets/readme/home.png"' in text),
    ("README referencia Análise", 'src="assets/readme/analysis.png"' in text),
    ("Alt Home presente", 'alt="Home do TFT Insight"' in text),
    ("Alt Análise presente", 'alt="Tela de análise do TFT Insight"' in text),
    ("Cards preservados", "### 🧩 Composições" in text and "### ⚔️ Contestação" in text),
    ("Arquitetura preservada", "## Arquitetura" in text),
    ("Setup preservado", "## Executando localmente" in text),
)

print("=" * 108)
print("#52C / ROADMAP 24.5 - SCREENSHOTS DO README")
print("=" * 108)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<78} {'OK' if ok else 'ERRO'}")

print("-" * 108)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#52C ROADMAP 24.5: SCREENSHOTS VALIDADOS")
