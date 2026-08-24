from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

engine = ROOT / "src/composition_intelligence_v2/services/composition_intelligence_v2.py"
presenter = ROOT / "src/composition_intelligence_v2/services/composition_player_presenter.py"

engine_text = engine.read_text(encoding="utf-8")
presenter_text = presenter.read_text(encoding="utf-8")

public_text = engine_text + "\n" + presenter_text

force_count = (
    public_text.count("Repetição não prova intenção de forçar composição.")
    + public_text.count("Repetição elevada não prova intenção de forçar composição.")
)

checks = [
    (
        "Support removido do texto público",
        "Carry, tank e support são inferências" not in public_text
        and "Carry, tanque e support são inferências" not in public_text,
    ),
    (
        "Guardrail de repetição aparece uma única vez",
        force_count == 1,
    ),
    (
        "Presenter mantém guardrail de repetição",
        "Repetição não prova intenção de forçar composição."
        in presenter_text,
    ),
    (
        "Engine mantém limitação sem Support",
        "Carry e tank são inferências baseadas nos sinais"
        in engine_text,
    ),
]

print("=" * 92)
print("#25 - VALIDAÇÃO TEXTUAL FINAL V2")
print("=" * 92)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i}] {name}: {'OK' if ok else 'ERRO'}")

print()
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#25 COMPOSIÇÕES AVANÇADAS: CONCLUÍDO")
else:
    sys.exit(1)
