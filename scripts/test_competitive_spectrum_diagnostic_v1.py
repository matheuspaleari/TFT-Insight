from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.benchmark.competitive_spectrum_diagnostic import (
    correlation_label,
    spectrum_band,
    theoretical_position,
)


def main() -> None:
    files = [
        ROOT / "src/benchmark/competitive_spectrum_diagnostic.py",
        ROOT / "scripts/diagnose_competitive_spectrum_v1.py",
    ]

    for path in files:
        ast.parse(
            path.read_text(encoding="utf-8")
        )

    checks = [
        (
            "Emerald IV início do Advanced",
            theoretical_position(
                benchmark_id="advanced",
                tier="EMERALD",
                division="IV",
                league_points=0,
            ) == 0.0,
        ),
        (
            "Emerald I antes de Diamond",
            theoretical_position(
                benchmark_id="advanced",
                tier="EMERALD",
                division="I",
                league_points=99,
            )
            <
            theoretical_position(
                benchmark_id="advanced",
                tier="DIAMOND",
                division="IV",
                league_points=0,
            ),
        ),
        (
            "Diamond I próximo do topo",
            theoretical_position(
                benchmark_id="advanced",
                tier="DIAMOND",
                division="I",
                league_points=99,
            ) > 0.99,
        ),
        (
            "Entrada",
            spectrum_band(0.10)[0]
            == "ENTRY",
        ),
        (
            "Consolidação",
            spectrum_band(0.30)[0]
            == "CONSOLIDATION",
        ),
        (
            "Avançado",
            spectrum_band(0.60)[0]
            == "ADVANCED",
        ),
        (
            "Transição",
            spectrum_band(0.90)[0]
            == "TRANSITION",
        ),
        (
            "Correlação quase zero é muito fraca",
            correlation_label(0.05)
            == "VERY_WEAK",
        ),
        (
            "Correlação moderada",
            correlation_label(0.30)
            == "MODERATE",
        ),
        (
            "Nenhuma regra cria peso de Coach",
            "coach_weight"
            not in (
                ROOT
                / "src/benchmark/competitive_spectrum_diagnostic.py"
            ).read_text(encoding="utf-8"),
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - COMPETITIVE SPECTRUM DIAGNOSTIC V1")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        1,
    ):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(
            "Status  : "
            f"{'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "COMPETITIVE SPECTRUM DIAGNOSTIC V1: VALIDADO"
        )
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
