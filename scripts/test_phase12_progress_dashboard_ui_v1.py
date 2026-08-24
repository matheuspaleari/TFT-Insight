from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

page_path = ROOT / "partner_platform/pages/benchmark_page.py"
route_path = ROOT / "src/integration_engine/api/routes/benchmark.py"
contract_path = ROOT / "src/integration_engine/contracts/benchmark.py"

page = page_path.read_text(encoding="utf-8")
route = route_path.read_text(encoding="utf-8")
contract = contract_path.read_text(encoding="utf-8")

ast.parse(page)
ast.parse(route)
ast.parse(contract)

checks = [
    ("UI possui Sua evolução", '"Sua evolução"' in page),
    ("UI possui histórico em construção", '"Histórico em construção"' in page),
    ("UI possui renderer de progresso", "def _render_progress_dashboard" in page),
    ("UI consome comparison.progress", 'comparison.get("progress")' in page),
    ("UI não usa elo como progresso", "não o elo" in page),
    ("UI possui gráfico longitudinal", "lines+markers" in page),
    ("UI preserva score não avaliado", "Score: **Não avaliado**" in page),
    ("API importa ProgressHistory", "ProgressHistoryService" in route),
    ("API importa ProgressSnapshot", "ProgressSnapshotService" in route),
    ("API importa ProgressIntelligence", "ProgressIntelligenceService" in route),
    ("API detecta milestones", "ProgressMilestoneService.detect" in route),
    ("API evita snapshot por refresh", "latest_signature != candidate_signature" in route),
    ("API publica progress", 'comparison_data["progress"]' in route),
    ("Contrato possui ProgressDashboard", "class BenchmarkProgressDashboard" in contract),
    ("Response expõe progress", "progress: BenchmarkProgressDashboard" in contract),
    ("Progress não troca Learning Priority", "primary_skill_id=priority_skill_id" in route),
    ("Progress parte do profile oficial", 'comparison_data["adaptive_coach"].get' in route),
    ("UI continua com Adaptive Coach", "def _render_adaptive_coach" in page),
    ("UI continua com histórico de treino", "_render_training_history" in page),
    ("Arquivos têm sintaxe válida", True),
]

print("=" * 82)
print("TFT INSIGHT - FASE 12.7 - PROGRESS DASHBOARD UI V1")
print("=" * 82)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{i}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 82)
print(f"PASSARAM: {passed}/{len(checks)}")
if passed == len(checks):
    print("FASE 12.7 PROGRESS DASHBOARD UI V1: VALIDADO")
    raise SystemExit(0)

print("FASE 12.7 PROGRESS DASHBOARD UI V1: AJUSTE NECESSÁRIO")
raise SystemExit(1)
