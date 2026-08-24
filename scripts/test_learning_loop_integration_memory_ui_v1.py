from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import PlayerRepository
from src.training.knowledge import get_tasks_for_skill
from src.training.models import TrainingMission
from src.training.services.learning_loop_orchestrator import (
    LearningLoopOrchestrator,
)
from src.training.services.pedagogical_memory_service import (
    PedagogicalMemoryService,
)


def cycle(
    *,
    cycle_id: str,
    skill_id: str,
    task_id: str,
    result: str,
    archived_at: str,
):
    return {
        "cycle_id": cycle_id,
        "archived_at": archived_at,
        "mission": {
            "games_completed": 5,
            "games_target": 5,
            "task": {
                "id": task_id,
                "skill_id": skill_id,
                "title": task_id,
            },
        },
        "evaluation": {
            "result": result,
            "confidence": "MODERATE",
            "confidence_score": 69.99,
            "evaluated_at": archived_at,
        },
    }


def completed_mission(
    skill_id: str,
    task_id: str,
):
    return {
        "task": {
            "skill_id": skill_id,
            "id": task_id,
        }
    }


def main() -> None:
    # Cenário atual histórico curto:
    current_like = LearningLoopOrchestrator.decide(
        priority_skill_id="leveling",
        completed_mission=completed_mission(
            "consistency",
            "define_simple_game_plan",
        ),
        training_history=[
            cycle(
                cycle_id="l1",
                skill_id="leveling",
                task_id="balance_level_and_stability",
                result="NEGATIVE",
                archived_at="2026-08-01T10:00:00+00:00",
            )
        ],
    )

    improving = LearningLoopOrchestrator.decide(
        priority_skill_id="leveling",
        completed_mission=completed_mission(
            "leveling",
            "plan_level_before_spending",
        ),
        training_history=[
            cycle(
                cycle_id="l2",
                skill_id="leveling",
                task_id="plan_level_before_spending",
                result="POSITIVE",
                archived_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="l1",
                skill_id="leveling",
                task_id="balance_level_and_stability",
                result="NEGATIVE",
                archived_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    two_negative = LearningLoopOrchestrator.decide(
        priority_skill_id="leveling",
        completed_mission=completed_mission(
            "leveling",
            "plan_level_before_spending",
        ),
        training_history=[
            cycle(
                cycle_id="l2",
                skill_id="leveling",
                task_id="plan_level_before_spending",
                result="NEGATIVE",
                archived_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="l1",
                skill_id="leveling",
                task_id="balance_level_and_stability",
                result="NEGATIVE",
                archived_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    three_negative = LearningLoopOrchestrator.decide(
        priority_skill_id="leveling",
        completed_mission=completed_mission(
            "leveling",
            "avoid_unplanned_rerolls",
        ),
        training_history=[
            cycle(
                cycle_id="l3",
                skill_id="leveling",
                task_id="avoid_unplanned_rerolls",
                result="NEGATIVE",
                archived_at="2026-08-15T10:00:00+00:00",
            ),
            cycle(
                cycle_id="l2",
                skill_id="leveling",
                task_id="balance_level_and_stability",
                result="NEGATIVE",
                archived_at="2026-08-10T10:00:00+00:00",
            ),
            cycle(
                cycle_id="l1",
                skill_id="leveling",
                task_id="plan_level_before_spending",
                result="NEGATIVE",
                archived_at="2026-08-01T10:00:00+00:00",
            ),
        ],
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        repo = PlayerRepository(
            players_directory=Path(temp_dir)
        )

        puuid = "memory-test"

        task = next(
            task
            for task in get_tasks_for_skill(
                "leveling"
            )
            if task.id
            == "plan_level_before_spending"
        )

        mission = TrainingMission(
            task=task,
            games_target=5,
            baseline_match_ids=(
                "b1",
                "b2",
            ),
        )

        memory_service = PedagogicalMemoryService(
            player_repository=repo
        )

        memory = memory_service.refresh(
            puuid=puuid,
            training_history=[
                cycle(
                    cycle_id="l1",
                    skill_id="leveling",
                    task_id="balance_level_and_stability",
                    result="NEGATIVE",
                    archived_at="2026-08-01T10:00:00+00:00",
                )
            ],
            current_mission=mission,
        )

        memory_service.record_decision(
            puuid=puuid,
            decision=current_like.to_dict(),
        )

        loaded = repo.load_pedagogical_memory(
            puuid=puuid
        )

        public = memory_service.public_payload(
            loaded
        )

        memory_path = (
            repo.get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "pedagogical_memory.json"
        )

        memory_checks = [
            memory_path.exists(),
            memory["current_skill_id"]
            == "leveling",
            memory["skills"]["leveling"]["trend"]
            == "INSUFFICIENT_HISTORY",
            memory["skills"]["leveling"]["current_difficulty"]
            == "FOUNDATION",
            isinstance(
                loaded.get(
                    "last_decision"
                ),
                dict,
            ),
            public["skills"]["leveling"]["anti_loop_action"]
            == "CONTINUE",
        ]

    route_path = (
        PROJECT_ROOT
        / "src/integration_engine/api/routes/benchmark.py"
    )
    contract_path = (
        PROJECT_ROOT
        / "src/integration_engine/contracts/benchmark.py"
    )
    page_path = (
        PROJECT_ROOT
        / "partner_platform/pages/benchmark_page.py"
    )
    player_service_path = (
        PROJECT_ROOT
        / "src/training/services/player_training_service.py"
    )

    for path in (
        route_path,
        contract_path,
        page_path,
        player_service_path,
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
    player_service = player_service_path.read_text(
        encoding="utf-8"
    )

    checks = [
        (
            "HOLD preserva Post-Cycle imediato",
            current_like.selected_task_id
            == "plan_level_before_spending",
        ),
        (
            "Histórico curto não sobe dificuldade",
            current_like.selected_difficulty
            == "FOUNDATION",
        ),
        (
            "Learning Priority continua sendo Skill-alvo",
            current_like.priority_skill_id
            == "leveling",
        ),
        (
            "IMPROVING gera ADVANCE_CANDIDATE",
            improving.progression_signal
            == "ADVANCE_CANDIDATE",
        ),
        (
            "IMPROVING pode avançar dificuldade",
            improving.selected_difficulty
            == "INTERMEDIATE",
        ),
        (
            "Dois NEGATIVE pedem reavaliação",
            two_negative.requires_priority_reassessment,
        ),
        (
            "Reavaliação retorna FOUNDATION",
            two_negative.selected_difficulty
            == "FOUNDATION",
        ),
        (
            "Três NEGATIVE consecutivos acionam cooldown",
            three_negative.anti_loop_action
            == "COOLDOWN_SKILL",
        ),
        (
            "Cooldown adia nova missão",
            three_negative.defer_new_mission,
        ),
        (
            "Memória é persistida",
            memory_checks[0],
        ),
        (
            "Memória conhece Skill atual",
            memory_checks[1],
        ),
        (
            "Memória guarda tendência",
            memory_checks[2],
        ),
        (
            "Memória guarda dificuldade atual",
            memory_checks[3],
        ),
        (
            "Memória preserva última decisão",
            memory_checks[4],
        ),
        (
            "Payload público expõe anti-loop",
            memory_checks[5],
        ),
        (
            "PlayerTrainingService usa LearningLoopOrchestrator",
            "LearningLoopOrchestrator.decide" in player_service,
        ),
        (
            "API atualiza memória pedagógica",
            "memory_service.refresh" in route,
        ),
        (
            "API expõe learning_state",
            '"learning_state": learning_state' in route,
        ),
        (
            "Contrato possui BenchmarkLearningState",
            "class BenchmarkLearningState" in contract,
        ),
        (
            "Contrato expõe task_difficulty",
            "task_difficulty" in contract,
        ),
        (
            "UI possui Estado de aprendizagem",
            "def _render_learning_state(" in page,
        ),
        (
            "UI renderiza learning state",
            "_render_learning_state(" in page[
                page.rfind("_render_training_mission("):
            ],
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - LEARNING LOOP INTEGRATION + MEMORY + UI V1"
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
    print("-" * 82)
    print("CENÁRIO CURTO")
    print("-" * 82)
    print(
        f"Skill        : {current_like.priority_skill_id}"
    )
    print(
        f"Anti-loop    : {current_like.anti_loop_action}"
    )
    print(
        f"Progressão   : {current_like.progression_signal}"
    )
    print(
        f"Task         : {current_like.selected_task_id}"
    )
    print(
        f"Dificuldade  : {current_like.selected_difficulty}"
    )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "LEARNING LOOP INTEGRATION + MEMORY + UI V1: VALIDADO"
        )
        raise SystemExit(0)

    print(
        "LEARNING LOOP INTEGRATION + MEMORY + UI V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
