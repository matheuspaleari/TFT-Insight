from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Permite executar o script diretamente a partir de scripts\,
# mantendo o padrão de imports "from src....".
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark_intelligence.service import BenchmarkIntelligenceService


BENCHMARKS = ("novice", "intermediate", "advanced", "expert", "elite")


def check(label: str, condition: bool) -> bool:
    status = "OK" if condition else "FALHOU"
    print(f"[{status}] {label}")
    return bool(condition)


def main() -> int:
    print("=" * 92)
    print("VALIDACAO 68 - BENCHMARKS COM METRICAS OPCIONAIS")
    print("=" * 92)

    service = BenchmarkIntelligenceService(project_root=ROOT)
    checks: list[bool] = []

    for benchmark_id in BENCHMARKS:
        try:
            overview = service.overview_for(
                benchmark_id=benchmark_id,
                include_players=False,
            )
        except Exception as exc:
            checks.append(
                check(
                    f"{benchmark_id}: overview nao gera excecao ({exc})",
                    False,
                )
            )
            continue

        metrics = overview.get("metrics", {})

        checks.append(
            check(
                f"{benchmark_id}: benchmark carregado",
                overview.get("benchmark_id") == benchmark_id,
            )
        )
        checks.append(
            check(
                f"{benchmark_id}: average_level preservado",
                "average_level" in metrics,
            )
        )
        checks.append(
            check(
                f"{benchmark_id}: placement_standard_deviation preservado",
                "placement_standard_deviation" in metrics,
            )
        )
        checks.append(
            check(
                f"{benchmark_id}: damage indisponivel nao vira distribuicao falsa",
                "average_damage_to_players" not in metrics,
            )
        )

    original_loader = service._load_group_benchmark

    def fake_loader(_: str):
        return {
            "name": "Fake",
            "players_analyzed": 1,
            "matches_analyzed": 1,
            "top4_rate": 50.0,
            "win_rate": 10.0,
            "average_placement": 4.5,
            "average_level": {
                "mean": 8.0,
                "median": 8.0,
                "minimum": 7.0,
                "maximum": 9.0,
                "first_quartile": 7.5,
                "third_quartile": 8.5,
            },
            "average_damage_to_players": None,
            "placement_standard_deviation": {
                "mean": None,
                "median": 2.0,
                "minimum": 1.0,
                "maximum": 3.0,
                "first_quartile": 1.5,
                "third_quartile": 2.5,
            },
        }

    service._load_group_benchmark = fake_loader

    try:
        fake = service.overview_for(
            benchmark_id="intermediate",
            include_players=False,
        )
        fake_metrics = fake["metrics"]

        checks.append(
            check(
                "estrutura parcial tambem e ignorada com seguranca",
                "placement_standard_deviation" not in fake_metrics
                and "average_damage_to_players" not in fake_metrics
                and "average_level" in fake_metrics,
            )
        )
    finally:
        service._load_group_benchmark = original_loader

    print("-" * 92)
    passed = sum(checks)
    total = len(checks)
    print(f"Checks aprovados: {passed}/{total}")

    if passed == total:
        print("RESULTADO: BENCHMARKS TOLERAM METRICAS OPCIONAIS SEM 500")
        return 0

    print("RESULTADO: VALIDACAO 68 COM PENDENCIAS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
