from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "contest": ROOT / "src" / "contest_intelligence" / "services" / "contest_player_presenter.py",
    "composition": ROOT / "src" / "composition_intelligence_v2" / "services" / "composition_player_presenter.py",
    "benchmark": ROOT / "src" / "integration_engine" / "services" / "benchmark_coach_context_builder.py",
}

checks = []

def check(label: str, condition: bool) -> None:
    checks.append((label, bool(condition)))
    print(("OK   " if condition else "ERRO ") + label)

texts = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}

print("=" * 100)
print("TFT INSIGHT — #60A DISPLAY NAMES / PUBLIC BOUNDARY")
print("=" * 100)

check("Contest usa UnitCatalogRepository", "UnitCatalogRepository" in texts["contest"])
check(
    "Contest não interpola latest.carry_character_id diretamente no texto público",
    "{latest.carry_character_id" not in texts["contest"],
)
check("Composition preserva carry_character_id interno", '"carry_character_id": profile.carry_character_id' in texts["composition"])
check("Composition adiciona carry_name público", '"carry_name": cls._display_name' in texts["composition"])
check("Composition preserva tank_character_id interno", '"tank_character_id": profile.tank_character_id' in texts["composition"])
check("Composition adiciona tank_name público", '"tank_name": cls._display_name' in texts["composition"])
check("Benchmark preserva most_used_carry_character_id", '"most_used_carry_character_id"' in texts["benchmark"])
check("Benchmark adiciona most_used_carry_name", '"most_used_carry_name"' in texts["benchmark"])
check("Benchmark adiciona best_carry_name", '"best_carry_name"' in texts["benchmark"])
check("Benchmark adiciona most_contested_unit_name", '"most_contested_unit_name"' in texts["benchmark"])
check("Benchmark adiciona latest_carry_name", '"latest_carry_name"' in texts["benchmark"])
check("Benchmark adiciona latest_contested_unit_names", '"latest_contested_unit_names"' in texts["benchmark"])

failed = [label for label, ok in checks if not ok]
print()
print(f"RESULTADO: {len(checks) - len(failed)}/{len(checks)} OK")
if failed:
    raise SystemExit("Falhas: " + "; ".join(failed))

print("IDs técnicos foram preservados; nomes amigáveis foram adicionados na fronteira pública.")
