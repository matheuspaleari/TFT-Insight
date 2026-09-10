from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
runner = ROOT / "scripts" / "run_challenger_item_benchmark.py"
source = runner.read_text(encoding="utf-8")
tree = ast.parse(source)

checks = []

def check(label: str, condition: bool) -> None:
    checks.append((label, bool(condition)))
    print(("OK   " if condition else "ERRO ") + label)

print("=" * 100)
print("TFT INSIGHT — #61A SELECTIVE ITEM-LEARNING RESET")
print("=" * 100)

check("--reset-learning existe", '"--reset-learning"' in source)
check("reset_learning_state existe", "def reset_learning_state()" in source)
check("cache de partidas não é apagado pelo reset seletivo", "MATCH_CACHE_DIRECTORY.glob" in source)
check("observações são removidas", "OBSERVATIONS_PATH" in source and "path.unlink()" in source)
check("processed_match_ids é reiniciado", 'index["processed_match_ids"] = []' in source)
check("failed_match_ids é reiniciado", 'index["failed_match_ids"] = {}' in source)
check("match_ids não é zerado", 'index["match_ids"] = {}' not in source)
check("reset completo original continua disponível", "def reset_state()" in source and "reset_state()" in source)
check("modos de reset não podem ser combinados", "args.reset and args.reset_learning" in source)

failed = [label for label, ok in checks if not ok]
print()
print(f"RESULTADO: {len(checks) - len(failed)}/{len(checks)} OK")
if failed:
    raise SystemExit("Falhas: " + "; ".join(failed))

print("Reset seletivo pronto: IDs/cache preservados; aprendizado será reprocessado.")
