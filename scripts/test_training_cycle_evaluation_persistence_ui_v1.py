from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import PlayerRepository


def main() -> None:
    checks: list[tuple[str, bool]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        repo = PlayerRepository(
            players_directory=Path(temp_dir)
        )

        puuid = "persistence-ui-test"
        player_dir = repo.get_player_directory(
            puuid=puuid
        )

        cycle_dir = (
            player_dir
            / "history"
            / "training_cycles"
        )
        cycle_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        cycle_id = "cycle-1"
        cycle_path = (
            cycle_dir
            / f"{cycle_id}.json"
        )

        repo._write_json(
            path=cycle_path,
            data={
                "cycle_id": cycle_id,
                "status": "completed",
                "mission": {
                    "games_completed": 5,
                    "games_target": 5,
                    "task": {
                        "id": "balance_level_and_stability",
                        "skill_id": "leveling",
                        "title": "Equilibrar nível e estabilidade",
                    },
                },
            },
        )

        evaluation = {
            "result": "NEGATIVE",
            "confidence": "MODERATE",
            "confidence_score": 69.99,
            "positive_metrics": 0,
            "stable_metrics": 0,
            "negative_metrics": 3,
            "before_sample_size": 29,
            "after_sample_size": 5,
            "reason": "3 de 3 métricas negativas.",
            "caveat": "Não prova causalidade.",
            "metric_evaluations": [
                {
                    "metric_id": "average_level",
                    "before": 8.38,
                    "after": 7.8,
                    "delta": -0.58,
                    "relative_change": -0.0692,
                    "direction": "negative",
                    "significance": "relevant",
                }
            ],
        }

        repo.save_training_cycle_evaluation(
            puuid=puuid,
            cycle_id=cycle_id,
            evaluation=evaluation,
        )

        loaded = repo.load_training_cycle(
            puuid=puuid,
            cycle_id=cycle_id,
        )

        checks.extend(
            [
                (
                    "Avaliação persistida no ciclo",
                    isinstance(
                        loaded.get("evaluation"),
                        dict,
                    ),
                ),
                (
                    "Resultado NEGATIVE preservado",
                    loaded["evaluation"]["result"]
                    == "NEGATIVE",
                ),
                (
                    "Confiança MODERATE preservada",
                    loaded["evaluation"]["confidence"]
                    == "MODERATE",
                ),
                (
                    "Missão original preservada",
                    loaded["mission"]["task"]["skill_id"]
                    == "leveling",
                ),
                (
                    "evaluated_at adicionado",
                    bool(
                        loaded["evaluation"].get(
                            "evaluated_at"
                        )
                    ),
                ),
            ]
        )

    files = [
        PROJECT_ROOT
        / "src"
        / "storage"
        / "player_repository.py",
        PROJECT_ROOT
        / "src"
        / "training"
        / "services"
        / "training_cycle_evaluation_service.py",
        PROJECT_ROOT
        / "src"
        / "integration_engine"
        / "api"
        / "routes"
        / "benchmark.py",
        PROJECT_ROOT
        / "src"
        / "integration_engine"
        / "contracts"
        / "benchmark.py",
        PROJECT_ROOT
        / "partner_platform"
        / "pages"
        / "benchmark_page.py",
    ]

    for path in files:
        ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

    route = files[2].read_text(
        encoding="utf-8"
    )
    contract = files[3].read_text(
        encoding="utf-8"
    )
    page = files[4].read_text(
        encoding="utf-8"
    )

    checks.extend(
        [
            (
                "API avalia ciclos pendentes",
                "evaluate_pending_cycles" in route,
            ),
            (
                "API expõe evaluation segura",
                '"evaluation": public_evaluation' in route,
            ),
            (
                "Contrato possui avaliação do histórico",
                "BenchmarkTrainingEvaluation" in contract,
            ),
            (
                "UI mostra mudança observada",
                "_TRAINING_RESULT_LABELS" in page,
            ),
            (
                "UI mostra deltas percentuais",
                "_training_delta_text" in page,
            ),
        ]
    )

    print("=" * 82)
    print(
        "TFT INSIGHT - TRAINING CYCLE EVALUATION PERSISTENCE + UI V1"
    )
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        start=1,
    ):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "EVALUATION PERSISTENCE + UI V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "EVALUATION PERSISTENCE + UI V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
