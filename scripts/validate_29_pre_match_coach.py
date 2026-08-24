from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
checks = []

def check(label, ok):
    checks.append((label, bool(ok)))
    print(f"[{'OK' if ok else 'ERRO'}] {label}")

component = ROOT / 'partner_platform/components/pre_match_coach.py'
page = ROOT / 'partner_platform/pages/benchmark_page.py'
check('Componente do Coach pré-partida existe', component.exists())
check('benchmark_page.py existe', page.exists())

for path in (component, page):
    try:
        ast.parse(path.read_text(encoding='utf-8'))
        check(f'Sintaxe válida: {path.name}', True)
    except SyntaxError as exc:
        print(exc)
        check(f'Sintaxe válida: {path.name}', False)

text = component.read_text(encoding='utf-8') if component.exists() else ''
page_text = page.read_text(encoding='utf-8') if page.exists() else ''
check('Consolida os 4 módulos avançados', all(x in text for x in ('composition', 'contest', 'economy', 'carry_item')))
check('Mantém missão como prioridade', 'não altera sua missão ativa' in text.lower())
check('Não trata histórico como causalidade', 'causalidade' in text.lower())
check('Não inventa telemetria', 'telemetria' in text.lower())
check('Integração adicionada à página', '_render_pre_match_coach_integration(' in page_text)
check('Botão único de plano pré-partida', 'Gerar plano pré-partida' in page_text)

passed = sum(ok for _, ok in checks)
print('\n' + '=' * 88)
print(f'PASSARAM: {passed}/{len(checks)}')
if passed == len(checks):
    print('#29 / ROADMAP 18 COACH PRÉ-PARTIDA CONSOLIDADO: VALIDADO')
    sys.exit(0)
print('#29: REQUER AJUSTES')
sys.exit(1)
