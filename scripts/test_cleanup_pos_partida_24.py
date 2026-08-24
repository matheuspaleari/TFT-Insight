
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "partner_platform/components/post_match_report.py"
text = FILE.read_text(encoding="utf-8")

checks = []

try:
    ast.parse(text)
    syntax_ok = True
except SyntaxError:
    syntax_ok = False

checks.extend([
    ("Arquivo possui sintaxe válida", syntax_ok),
    ("Next Match Plan continua renderizado", "_render_next_match_plan(report)" in text),
    ("Título oficial do plano permanece", '"Plano para a próxima partida"' in text),
    ("Ação principal permanece", 'eyebrow="Ação principal"' in text),
    ("Fique de olho permanece", 'st.markdown("#### Fique de olho")' in text),
    ("Preserve permanece", 'eyebrow="Preserve"' in text),
    ("Lembrete do Coach permanece", 'st.caption("Lembrete do Coach")' in text),
    ("Guardrail publishable continua respeitado", 'plan.get("publishable", False)' in text),
    ("Bloco antigo Para o próximo jogo removido", 'eyebrow="Para o próximo jogo"' not in text),
    ("Título Leve uma ideia, não dez removido", '"Leve uma ideia, não dez"' not in text),
    ("coach_takeaway não cria segundo CTA", 'report.get("coach_takeaway"' not in text),
    ("Limitações continuam disponíveis", '"O que ainda não conseguimos medir"' in text),
    ("Detalhes técnicos continuam disponíveis", '"Detalhes técnicos da análise"' in text),
])

print("=" * 96)
print("TFT INSIGHT - #24 CLEANUP PÓS-PARTIDA")
print("=" * 96)

passed = 0
for index, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{index}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 96)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed == len(checks):
    print("#24 CLEANUP PÓS-PARTIDA: VALIDADO")
else:
    print("#24 CLEANUP PÓS-PARTIDA: FALHOU")
    raise SystemExit(1)
