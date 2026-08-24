from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark.competitive_spectrum_diagnostic import (
    BENCHMARK_SPECTRA,
    CompetitiveSpectrumDiagnostic,
)


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "benchmark_ids",
        nargs="*",
        choices=tuple(BENCHMARK_SPECTRA),
    )
    args = parser.parse_args()

    diagnostic = CompetitiveSpectrumDiagnostic()

    benchmark_ids = (
        args.benchmark_ids
        or diagnostic.available_catalogs()
    )

    if not benchmark_ids:
        print("Nenhum catálogo individual disponível.")
        raise SystemExit(1)

    print("=" * 92)
    print("TFT INSIGHT - COMPETITIVE SPECTRUM DIAGNOSTIC V1")
    print("=" * 92)

    for benchmark_id in benchmark_ids:
        print()
        print("=" * 92)
        print(
            "GRUPO COMPETITIVO: "
            f"{benchmark_id.upper()}"
        )
        print("=" * 92)

        report = diagnostic.analyze(
            benchmark_id
        )

        json_path, csv_path = (
            diagnostic.save_report(
                report
            )
        )

        print()
        print("DISTRIBUIÇÃO DE ELO")
        print("-" * 92)

        for rank, count in report[
            "rank_distribution"
        ].items():
            print(
                f"{rank:<20} : {count:>3}"
            )

        print()
        print("FAIXAS DO ESPECTRO")
        print("-" * 92)

        for band, count in report[
            "band_distribution"
        ].items():
            print(
                f"{band:<20} : {count:>3}"
            )

        print()
        print("SINAIS MÉTRICA × PROGRESSÃO")
        print("-" * 92)
        print(
            f"{'Métrica':<34}"
            f"{'Spearman':>12}"
            f"{'Sinal':>12}"
            f"{'Força':>18}"
        )

        for item in report[
            "metric_correlations"
        ]:
            raw = item[
                "raw_spearman"
            ]
            signal = item[
                "progression_signal"
            ]

            raw_text = (
                f"{raw:+.3f}"
                if raw is not None
                else "-"
            )
            signal_text = (
                f"{signal:+.3f}"
                if signal is not None
                else "-"
            )

            print(
                f"{item['metric']:<34}"
                f"{raw_text:>12}"
                f"{signal_text:>12}"
                f"{item['interpretation']:>18}"
            )

        print()
        print("MÉDIAS POR FAIXA")
        print("-" * 92)

        for band, payload in report[
            "band_metric_summary"
        ].items():
            print()
            print(
                f"{band} "
                f"({payload['players']} jogadores)"
            )

            for metric, value in payload[
                "metrics"
            ].items():
                value_text = (
                    f"{value:.3f}"
                    if value is not None
                    else "-"
                )

                print(
                    f"  {metric:<32}: "
                    f"{value_text}"
                )

        print()
        print("ARQUIVOS")
        print("-" * 92)
        print(json_path)
        print(csv_path)

    print()
    print("=" * 92)
    print("IMPORTANTE")
    print("=" * 92)
    print(
        "Spearman mede associação monotônica entre posição competitiva "
        "e métrica. Não implica causalidade."
    )
    print(
        "Nenhum peso do Coach é alterado por este diagnóstico."
    )
    print(
        "O percentil empírico usa apenas os jogadores realmente presentes "
        "no catálogo do grupo."
    )

    print()
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'GRUPO COMPETITIVO' até o final."
    )


if __name__ == "__main__":
    main()
