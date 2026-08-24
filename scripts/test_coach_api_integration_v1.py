from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = [
    ROOT / "src/coach/services/coach_pipeline_service.py",
    ROOT / "src/coach/engine/coach_engine.py",
    ROOT / "src/integration_engine/api/routes/benchmark.py",
    ROOT / "src/integration_engine/contracts/benchmark.py",
]

checks = []
for p in paths:
    ast.parse(p.read_text(encoding="utf-8"))
    checks.append((f"{p.name} sintaxe", True))

pipeline = paths[0].read_text(encoding="utf-8")
engine = paths[1].read_text(encoding="utf-8")
route = paths[2].read_text(encoding="utf-8")
contract = paths[3].read_text(encoding="utf-8")

checks += [
    ("Pipeline sem PlayerAnalysisService", "PlayerAnalysisService" not in pipeline),
    ("Pipeline sem CachedMatchService", "CachedMatchService" not in pipeline),
    ("CoachEngine delega ao pipeline", "self.pipeline_service.run" in engine),
    ("API usa CoachPipelineService", "CoachPipelineService().run" in route),
    ("Contrato expõe training", "training: BenchmarkTrainingContext | None" in contract),
]

print("=" * 82)
print("TFT INSIGHT - COACH API INTEGRATION V1")
print("=" * 82)
passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
print("\n" + "=" * 82)
print(f"PASSARAM: {passed}/{len(checks)}")
raise SystemExit(0 if passed == len(checks) else 1)
