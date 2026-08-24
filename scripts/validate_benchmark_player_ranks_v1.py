from __future__ import annotations
import argparse
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.benchmark import BENCHMARK_GROUP_CONFIGURATIONS, BenchmarkRankValidationService

DEFAULT_IDS = tuple(BENCHMARK_GROUP_CONFIGURATIONS.keys())

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_ids", nargs="*", choices=DEFAULT_IDS)
    parser.add_argument(
        "--drift-threshold",
        type=float,
        default=0.20,
        help="Percentual fora do grupo que recomenda reconstrução.",
    )
    args = parser.parse_args()
    ids = tuple(args.benchmark_ids) or DEFAULT_IDS

    print("=" * 88)
    print("TFT INSIGHT - BENCHMARK RANK VALIDATION V1")
    print("=" * 88)

    service = BenchmarkRankValidationService()
    summaries = []

    for benchmark_id in ids:
        print()
        print("=" * 88)
        print(f"BENCHMARK: {benchmark_id}")
        print("=" * 88)
        try:
            result = service.validate(benchmark_id=benchmark_id)
        except FileNotFoundError as error:
            print(f"IGNORADO: {error}")
            continue

        needs_refresh = result["outside_group_ratio"] >= args.drift_threshold
        result["needs_benchmark_refresh"] = needs_refresh
        summaries.append(result)

        print()
        print(f"Mudanças observadas : {result['changed']}")
        print(f"Mudança de tier      : {result['tier_changed']}")
        print(f"Mudança de divisão   : {result['division_changed']}")
        print(f"Mudança de LP        : {result['lp_changed']}")
        print(f"Fora do grupo        : {result['outside_group']}/{result['players']}")
        print(f"Recomenda refresh    : {'SIM' if needs_refresh else 'NÃO'}")

    print()
    print("=" * 88)
    print("RESUMO")
    print("=" * 88)
    for item in summaries:
        print(
            f"{item['benchmark_id']:<14} | "
            f"alterados={item['changed']:<3} | "
            f"fora={item['outside_group']:<3} | "
            f"refresh={'SIM' if item['needs_benchmark_refresh'] else 'NÃO'}"
        )

    print()
    print("IMPORTANTE")
    print("Gold I -> Gold IV atualiza catálogo e histórico de elo, mas não reconstrói sozinho as métricas agregadas.")
    print("Rebuild é recomendado quando jogadores começam a sair do espectro do grupo em quantidade relevante.")

if __name__ == "__main__":
    main()
