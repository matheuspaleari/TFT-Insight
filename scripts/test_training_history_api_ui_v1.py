from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.integration_engine.api.routes.benchmark import (
    _training_history_payload,
)


def main() -> None:
    fake_cycles = [
        {
            "cycle_id": "cycle-current",
            "archived_at": "2026-08-13T15:00:00+00:00",
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
        {
            "cycle_id": "cycle-old",
            "archived_at": "2026-08-12T15:00:00+00:00",
            "status": "completed",
            "mission": {
                "games_completed": 5,
                "games_target": 5,
                "task": {
                    "id": "consistency_test",
                    "skill_id": "consistency",
                    "title": "Decisões mais estáveis",
                },
            },
        },
    ]

    payload = _training_history_payload(
        cycles=fake_cycles,
        current_completed_mission_id="cycle-current",
    )

    checks = [
        (
            "Ciclo atual 5/5 não duplica no histórico da mesma tela",
            len(payload) == 1,
        ),
        (
            "Ciclo anterior permanece no histórico",
            payload[0]["skill_id"] == "consistency",
        ),
        (
            "Skill recebe nome amigável",
            payload[0]["skill_name"] == "Consistência",
        ),
        (
            "Payload preserva progresso concluído",
            payload[0]["games_completed"] == 5
            and payload[0]["games_target"] == 5,
        ),
        (
            "Payload não expõe match_ids",
            "completed_match_ids" not in payload[0]
            and "baseline_match_ids" not in payload[0],
        ),
    ]

    route_path = (
        PROJECT_ROOT
        / "src"
        / "integration_engine"
        / "api"
        / "routes"
        / "benchmark.py"
    )
    contract_path = (
        PROJECT_ROOT
        / "src"
        / "integration_engine"
        / "contracts"
        / "benchmark.py"
    )
    page_path = (
        PROJECT_ROOT
        / "partner_platform"
        / "pages"
        / "benchmark_page.py"
    )

    for path in (
        route_path,
        contract_path,
        page_path,
    ):
        ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

    route = route_path.read_text(
        encoding="utf-8"
    )
    contract = contract_path.read_text(
        encoding="utf-8"
    )
    page = page_path.read_text(
        encoding="utf-8"
    )

    checks.extend(
        [
            (
                "API lê list_training_cycles",
                "list_training_cycles" in route,
            ),
            (
                "Contrato expõe history",
                "history: list[BenchmarkTrainingHistoryItem]" in contract,
            ),
            (
                "UI possui histórico de treino",
                "def _render_training_history(" in page,
            ),
            (
                "UI usa somente training recebido",
                'comparison.get("training")' in page,
            ),
            (
                "UI não acessa PlayerRepository",
                "PlayerRepository" not in page,
            ),
        ]
    )

    print("=" * 82)
    print("TFT INSIGHT - TRAINING HISTORY API/UI V1")
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
            "TRAINING HISTORY API/UI V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "TRAINING HISTORY API/UI V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
