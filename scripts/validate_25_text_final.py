from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

bad_support = []
force_lines = []

for path in ROOT.rglob("*.py"):
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue

    if (
        "Carry, tank e support são inferências"
        in text
        or "Carry, tanque e support são inferências"
        in text
    ):
        bad_support.append(str(path.relative_to(ROOT)))

    for line in text.splitlines():
        low = line.lower()
        if (
            "repetição" in low
            and "não prova intenção de forçar composição" in low
        ):
            force_lines.append(
                (str(path.relative_to(ROOT)), line.strip())
            )

print("=" * 92)
print("#25 - VALIDAÇÃO TEXTUAL FINAL")
print("=" * 92)

checks = [
    ("Support removido do guardrail público", not bad_support),
    ("Guardrail de repetição não está duplicado", len(force_lines) <= 1),
]

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i}] {name}: {'OK' if ok else 'ERRO'}")

print()
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#25 COMPOSIÇÕES AVANÇADAS: CONCLUÍDO")
else:
    if bad_support:
        print("Support encontrado em:", *bad_support, sep="\n- ")
    if len(force_lines) > 1:
        print("Guardrails encontrados:")
        for item in force_lines:
            print("-", item)
    sys.exit(1)
