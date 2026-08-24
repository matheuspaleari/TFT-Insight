from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.intelligence.global_priority_engine import build_global_priority


def bm(metric, label, title, gap):
    return {
        "role": "priority",
        "metric": metric,
        "metric_label": label,
        "title": title,
        "message": title,
        "priority": 1,
        "evidence": {"relative_gap": gap, "percentile": None},
    }


def st(metric, label, title, role, weight, confidence=0.0, impact_label=""):
    return {
        "role": role,
        "metric": metric,
        "metric_label": label,
        "title": title,
        "message": title,
        "priority": 1 if role == "priority" else None,
        "strategic_weight": weight,
        "evidence": {
            "confidence": confidence,
            "placement_impact_label": impact_label,
        },
    }


SCENARIOS = [
    (
        "Contestação forte com impacto alto",
        "contest_pattern",
        [
            st("contest_pattern", "Contestação", "Contestação é prioridade", "priority", 100, 82, "alto"),
            st("economy_pattern", "Economia", "Economia saudável", "strength", 50),
        ],
        [bm("average_level", "Nível médio", "Nível abaixo da referência", -18)],
    ),
    (
        "Contestação sem piora + benchmark grande",
        "average_level",
        [
            st("contest_pattern", "Contestação", "Contestação frequente sem piora", "priority", 72, 78, "sem_piora_observada"),
        ],
        [bm("average_level", "Nível médio", "Gap grande de nível", -28)],
    ),
    (
        "Problema econômico forte",
        "economy_pattern",
        [
            st("economy_pattern", "Economia", "Conversão de recursos é prioridade", "adjustment", 92, 84),
            st("contest_pattern", "Contestação", "Contestação moderada", "adjustment", 58, 70, "leve"),
        ],
        [bm("top4_rate", "Taxa de Top 4", "Top 4 abaixo da referência", -12)],
    ),
    (
        "Composição rígida",
        "composition_pattern",
        [
            st("composition_pattern", "Composição", "Concentração excessiva", "adjustment", 88, 80),
            st("economy_pattern", "Economia", "Economia forte", "strength", 50),
        ],
        [bm("win_rate", "Taxa de vitória", "Vitória abaixo da referência", -10)],
    ),
    (
        "Benchmark claramente dominante",
        "top4_rate",
        [
            st("contest_pattern", "Contestação", "Contestação leve", "adjustment", 48, 65, "neutro"),
        ],
        [bm("top4_rate", "Taxa de Top 4", "Top 4 muito abaixo da referência", -30)],
    ),
    (
        "Sem problema crítico",
        None,
        [
            st("composition_pattern", "Composição", "Boa flexibilidade", "strength", 45),
            st("economy_pattern", "Economia", "Economia forte", "strength", 50),
        ],
        [],
    ),
]


def main():
    print("=" * 72)
    print("TFT INSIGHT - GLOBAL PRIORITY VALIDATION")
    print("=" * 72)

    passed = 0

    for i, (name, expected, strategic, benchmark) in enumerate(SCENARIOS, 1):
        result = build_global_priority(
            strategic_messages=strategic,
            benchmark_messages=benchmark,
            max_adjustments=2,
            max_strengths=2,
        )

        actual = result.primary.get("metric") if result.primary else None
        ok = actual == expected
        passed += int(ok)

        print()
        print(f"[{i}] {name}")
        print(f"Resultado : {actual}")
        print(f"Esperado  : {expected}")
        print(f"Status    : {'OK' if ok else 'ERRO'}")

        if result.primary:
            print(f"Origem    : {result.primary.get('source')}")
            print(f"Score     : {result.primary.get('global_score')}")

    print()
    print("=" * 72)
    print(f"PASSARAM: {passed}/{len(SCENARIOS)}")

    if passed == len(SCENARIOS):
        print("GLOBAL PRIORITY V1: VALIDADA")
        raise SystemExit(0)

    print("GLOBAL PRIORITY V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
