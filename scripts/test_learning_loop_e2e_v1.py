from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.training.knowledge import get_tasks_for_skill
from src.training.models import TrainingMission
from src.training.services.learning_loop_orchestrator import (
    LearningLoopOrchestrator,
)
from src.training.services.pedagogical_memory_service import (
    PedagogicalMemoryService,
)
from src.training.services.player_training_service import (
    PlayerTrainingService,
)


def task(
    skill_id: str,
    task_id: str,
):
    return next(
        item
        for item in get_tasks_for_skill(
            skill_id
        )
        if item.id == task_id
    )


def mission(
    *,
    skill_id: str,
    task_id: str,
    completed: int,
    target: int = 5,
    mission_id: str,
) -> TrainingMission:
    return TrainingMission(
        task=task(
            skill_id,
            task_id,
        ),
        games_target=target,
        games_completed=completed,
        mission_id=mission_id,
        baseline_match_ids=tuple(
            f"base-{mission_id}-{i}"
            for i in range(30)
        ),
        completed_match_ids=tuple(
            f"done-{mission_id}-{i}"
            for i in range(completed)
        ),
    )


def archived_cycle(
    *,
    cycle_id: str,
    skill_id: str,
    task_id: str,
    result: str | None,
    archived_at: str,
) -> dict:
    item = {
        "cycle_id": cycle_id,
        "archived_at": archived_at,
        "status": "completed",
        "mission": {
            "mission_id": cycle_id,
            "games_target": 5,
            "games_completed": 5,
            "task": task(
                skill_id,
                task_id,
            ).to_dict(),
        },
    }

    if result is not None:
        item["evaluation"] = {
            "result": result,
            "confidence": "MODERATE",
            "confidence_score": 69.99,
            "evaluated_at": archived_at,
        }

    return item


class FakeRepository:
    def __init__(
        self,
        *,
        current: TrainingMission | None,
        history: list[dict] | None = None,
    ) -> None:
        self.current = current
        self.history = list(
            history or []
        )
        self.memory = None
        self.saved_missions: list[
            TrainingMission
        ] = []
        self.archived_ids: list[str] = []

    def load_training_mission(
        self,
        *,
        puuid: str,
    ):
        return self.current

    def save_training_mission(
        self,
        *,
        puuid: str,
        mission: TrainingMission,
    ):
        self.current = mission
        self.saved_missions.append(
            mission
        )
        return Path(
            f"fake/{puuid}/training/current.json"
        )

    def archive_training_cycle(
        self,
        *,
        puuid: str,
        mission: TrainingMission,
    ):
        existing = next(
            (
                cycle
                for cycle in self.history
                if cycle.get(
                    "cycle_id"
                )
                == mission.mission_id
            ),
            None,
        )

        if existing is None:
            self.history.insert(
                0,
                {
                    "cycle_id": mission.mission_id,
                    "archived_at": (
                        "2026-08-20T12:00:00+00:00"
                    ),
                    "status": "completed",
                    "mission": mission.to_dict(),
                },
            )

        if (
            mission.mission_id
            not in self.archived_ids
        ):
            self.archived_ids.append(
                mission.mission_id
            )

        return Path(
            f"fake/{puuid}/history/"
            f"{mission.mission_id}.json"
        )

    def list_training_cycles(
        self,
        *,
        puuid: str,
    ):
        return list(
            self.history
        )

    def set_evaluation(
        self,
        *,
        cycle_id: str,
        result: str,
    ) -> None:
        cycle = next(
            item
            for item in self.history
            if item.get(
                "cycle_id"
            )
            == cycle_id
        )

        cycle["evaluation"] = {
            "result": result,
            "confidence": "MODERATE",
            "confidence_score": 69.99,
            "evaluated_at": (
                "2026-08-20T12:05:00+00:00"
            ),
        }

    def load_pedagogical_memory(
        self,
        *,
        puuid: str,
    ):
        return self.memory

    def save_pedagogical_memory(
        self,
        *,
        puuid: str,
        memory: dict,
    ):
        self.memory = dict(
            memory
        )
        return Path(
            f"fake/{puuid}/learning/"
            "pedagogical_memory.json"
        )

    @staticmethod
    def _utc_now():
        return (
            "2026-08-20T12:10:00+00:00"
        )


def plan(
    skill_id: str,
):
    return SimpleNamespace(
        primary_skill_id=skill_id,
        games_target=5,
    )


def scenario_active_protection():
    active = mission(
        skill_id="consistency",
        task_id="define_simple_game_plan",
        completed=3,
        mission_id="active-3-5",
    )

    repo = FakeRepository(
        current=active
    )

    service = PlayerTrainingService(
        player_repository=repo
    )

    returned = (
        service.get_or_create_mission_from_plan(
            puuid="p",
            training_plan=plan(
                "leveling"
            ),
            baseline_match_ids=(
                "new-1",
                "new-2",
            ),
        )
    )

    return (
        returned,
        repo,
    )


def scenario_improving_full_transition():
    current = mission(
        skill_id="leveling",
        task_id="plan_level_before_spending",
        completed=4,
        mission_id="leveling-positive-current",
    )

    old_negative = archived_cycle(
        cycle_id="leveling-old-negative",
        skill_id="leveling",
        task_id="balance_level_and_stability",
        result="NEGATIVE",
        archived_at="2026-08-10T10:00:00+00:00",
    )

    repo = FakeRepository(
        current=current,
        history=[
            old_negative,
        ],
    )

    first_run = PlayerTrainingService(
        player_repository=repo
    )

    # A quinta partida chega.
    matches = (
        "new-match-5",
        *current.baseline_match_ids[:29],
    )

    completed = (
        first_run.sync_mission_progress(
            puuid="p",
            current_match_ids=matches,
        )
    )

    # Na mesma análise, 5/5 continua visível.
    visible_5_5 = (
        first_run.get_or_create_mission_from_plan(
            puuid="p",
            training_plan=plan(
                "leveling"
            ),
            baseline_match_ids=matches,
        )
    )

    # A etapa de avaliação do ciclo acontece depois do pipeline.
    repo.set_evaluation(
        cycle_id=current.mission_id,
        result="POSITIVE",
    )

    # Próxima análise: usa histórico já avaliado.
    second_run = PlayerTrainingService(
        player_repository=repo
    )

    new_baseline = tuple(
        f"next-window-{i}"
        for i in range(30)
    )

    next_mission = (
        second_run.get_or_create_mission_from_plan(
            puuid="p",
            training_plan=plan(
                "leveling"
            ),
            baseline_match_ids=new_baseline,
        )
    )

    memory_service = PedagogicalMemoryService(
        player_repository=repo
    )

    memory = memory_service.refresh(
        puuid="p",
        training_history=repo.history,
        current_mission=next_mission,
    )

    return (
        completed,
        visible_5_5,
        next_mission,
        repo,
        memory,
        new_baseline,
    )


def scenario_two_negative_reassess():
    current = mission(
        skill_id="leveling",
        task_id="plan_level_before_spending",
        completed=5,
        mission_id="leveling-negative-current",
    )

    history = [
        archived_cycle(
            cycle_id=current.mission_id,
            skill_id="leveling",
            task_id="plan_level_before_spending",
            result="NEGATIVE",
            archived_at="2026-08-20T10:00:00+00:00",
        ),
        archived_cycle(
            cycle_id="leveling-negative-old",
            skill_id="leveling",
            task_id="balance_level_and_stability",
            result="NEGATIVE",
            archived_at="2026-08-10T10:00:00+00:00",
        ),
    ]

    repo = FakeRepository(
        current=current,
        history=history,
    )

    service = PlayerTrainingService(
        player_repository=repo
    )

    new_mission = (
        service.get_or_create_mission_from_plan(
            puuid="p",
            training_plan=plan(
                "leveling"
            ),
            baseline_match_ids=(
                "window-a",
                "window-b",
            ),
        )
    )

    decision = (
        LearningLoopOrchestrator.decide(
            priority_skill_id="leveling",
            completed_mission=current.to_dict(),
            training_history=repo.history,
        )
    )

    return (
        new_mission,
        decision,
        repo,
    )


def scenario_stable_rotate():
    current = mission(
        skill_id="consistency",
        task_id="review_one_decision_per_match",
        completed=5,
        mission_id="consistency-stable-current",
    )

    history = [
        archived_cycle(
            cycle_id=current.mission_id,
            skill_id="consistency",
            task_id="review_one_decision_per_match",
            result="STABLE",
            archived_at="2026-08-20T10:00:00+00:00",
        ),
        archived_cycle(
            cycle_id="consistency-stable-old",
            skill_id="consistency",
            task_id="review_one_decision_per_match",
            result="STABLE",
            archived_at="2026-08-10T10:00:00+00:00",
        ),
    ]

    decision = (
        LearningLoopOrchestrator.decide(
            priority_skill_id="consistency",
            completed_mission=current.to_dict(),
            training_history=history,
        )
    )

    return decision


def scenario_cooldown():
    current = mission(
        skill_id="leveling",
        task_id="avoid_unplanned_rerolls",
        completed=5,
        mission_id="leveling-neg-3",
    )

    history = [
        archived_cycle(
            cycle_id="leveling-neg-3",
            skill_id="leveling",
            task_id="avoid_unplanned_rerolls",
            result="NEGATIVE",
            archived_at="2026-08-20T10:00:00+00:00",
        ),
        archived_cycle(
            cycle_id="leveling-neg-2",
            skill_id="leveling",
            task_id="balance_level_and_stability",
            result="NEGATIVE",
            archived_at="2026-08-15T10:00:00+00:00",
        ),
        archived_cycle(
            cycle_id="leveling-neg-1",
            skill_id="leveling",
            task_id="plan_level_before_spending",
            result="NEGATIVE",
            archived_at="2026-08-10T10:00:00+00:00",
        ),
    ]

    repo = FakeRepository(
        current=current,
        history=history,
    )

    service = PlayerTrainingService(
        player_repository=repo
    )

    save_count_before = len(
        repo.saved_missions
    )

    returned = (
        service.get_or_create_mission_from_plan(
            puuid="p",
            training_plan=plan(
                "leveling"
            ),
            baseline_match_ids=(
                "future-a",
                "future-b",
            ),
        )
    )

    decision = (
        LearningLoopOrchestrator.decide(
            priority_skill_id="leveling",
            completed_mission=current.to_dict(),
            training_history=repo.history,
        )
    )

    return (
        returned,
        decision,
        repo,
        save_count_before,
    )


def main() -> None:
    active, active_repo = (
        scenario_active_protection()
    )

    (
        completed,
        visible_5_5,
        next_mission,
        improving_repo,
        improving_memory,
        new_baseline,
    ) = scenario_improving_full_transition()

    (
        reassess_mission,
        reassess_decision,
        reassess_repo,
    ) = scenario_two_negative_reassess()

    stable_decision = (
        scenario_stable_rotate()
    )

    (
        cooldown_returned,
        cooldown_decision,
        cooldown_repo,
        cooldown_save_before,
    ) = scenario_cooldown()

    checks = [
        # Active mission protection.
        (
            "Missão 3/5 não é interrompida",
            active.mission_id
            == "active-3-5",
        ),
        (
            "3/5 não é arquivado",
            not active_repo.archived_ids,
        ),
        (
            "3/5 não cria nova missão",
            not active_repo.saved_missions,
        ),

        # 4/5 -> 5/5.
        (
            "Quinta partida leva a 5/5",
            completed is not None
            and completed.games_completed == 5
            and completed.is_completed,
        ),
        (
            "5/5 é arquivado",
            completed.mission_id
            in improving_repo.archived_ids,
        ),
        (
            "Mesma análise mantém 5/5 visível",
            visible_5_5.mission_id
            == completed.mission_id,
        ),

        # Evaluation -> next run -> trend -> progression.
        (
            "Avaliação POSITIVE foi anexada ao ciclo",
            improving_repo.history[0]
            .get("evaluation", {})
            .get("result")
            == "POSITIVE",
        ),
        (
            "NEGATIVE -> POSITIVE gera missão nova",
            next_mission.mission_id
            != completed.mission_id,
        ),
        (
            "Nova missão começa 0/5",
            next_mission.games_completed == 0
            and next_mission.games_target == 5,
        ),
        (
            "Nova missão recebe baseline novo",
            tuple(
                next_mission.baseline_match_ids
            )
            == new_baseline,
        ),
        (
            "NEGATIVE -> POSITIVE sobe para INTERMEDIATE",
            next_mission.task.difficulty
            == "INTERMEDIATE",
        ),
        (
            "Progressão escolhe balance_level_and_stability",
            next_mission.task.id
            == "balance_level_and_stability",
        ),
        (
            "Memória registra tendência IMPROVING",
            improving_memory["skills"]
            ["leveling"]["trend"]
            == "IMPROVING",
        ),
        (
            "Memória registra dificuldade INTERMEDIATE",
            improving_memory["skills"]
            ["leveling"]["current_difficulty"]
            == "INTERMEDIATE",
        ),
        (
            "Última decisão do Learning Loop é persistida",
            isinstance(
                improving_repo.memory.get(
                    "last_decision"
                ),
                dict,
            ),
        ),

        # Reassessment.
        (
            "NEGATIVE -> NEGATIVE pede REASSESS",
            reassess_decision.anti_loop_action
            == "REASSESS",
        ),
        (
            "REASSESS solicita reavaliar prioridade",
            reassess_decision
            .requires_priority_reassessment,
        ),
        (
            "REASSESS retorna para FOUNDATION",
            reassess_mission.task.difficulty
            == "FOUNDATION",
        ),
        (
            "REASSESS cria missão 0/5",
            reassess_mission.games_completed
            == 0,
        ),

        # Stable rotation.
        (
            "STABLE -> STABLE detecta STABLE",
            stable_decision.trend
            == "STABLE",
        ),
        (
            "STABLE repetido rotaciona task",
            stable_decision.anti_loop_action
            == "ROTATE_TASK",
        ),
        (
            "ROTATE não aumenta dificuldade",
            stable_decision.selected_difficulty
            in {
                "FOUNDATION",
                "INTERMEDIATE",
            },
        ),

        # Cooldown.
        (
            "3 NEGATIVE consecutivos acionam COOLDOWN",
            cooldown_decision.anti_loop_action
            == "COOLDOWN_SKILL",
        ),
        (
            "COOLDOWN marca defer_new_mission",
            cooldown_decision.defer_new_mission,
        ),
        (
            "COOLDOWN mantém 5/5 atual",
            cooldown_returned.mission_id
            == "leveling-neg-3",
        ),
        (
            "COOLDOWN não salva nova missão",
            len(
                cooldown_repo.saved_missions
            )
            == cooldown_save_before,
        ),

        # Architectural contract.
        (
            "Learning Priority permanece Skill de entrada",
            cooldown_decision.priority_skill_id
            == "leveling",
        ),
        (
            "Loop não troca Skill por histórico",
            reassess_decision.priority_skill_id
            == "leveling",
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - FASE 10.8 - END-TO-END LEARNING LOOP V1"
    )
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        start=1,
    ):
        passed += int(ok)

        print()
        print(
            f"[{index}] {name}"
        )
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("-" * 82)
    print("FLUXO POSITIVO SIMULADO")
    print("-" * 82)
    print(
        "4/5 -> nova partida -> 5/5 -> arquiva -> "
        "mantém 5/5 visível"
    )
    print(
        "-> avaliação POSITIVE -> próxima análise"
    )
    print(
        "-> NEGATIVE + POSITIVE = IMPROVING"
    )
    print(
        "-> ADVANCE_CANDIDATE"
    )
    print(
        "-> FOUNDATION -> INTERMEDIATE"
    )
    print(
        "-> nova missão: "
        f"{next_mission.task.id} "
        f"({next_mission.task.difficulty}) "
        f"{next_mission.games_completed}/"
        f"{next_mission.games_target}"
    )

    print()
    print("-" * 82)
    print("FLUXO DE PROTEÇÃO SIMULADO")
    print("-" * 82)
    print(
        "NEGATIVE -> NEGATIVE -> NEGATIVE"
    )
    print(
        "-> REGRESSING"
    )
    print(
        "-> COOLDOWN_SKILL"
    )
    print(
        "-> nova missão adiada"
    )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "END-TO-END LEARNING LOOP V1: VALIDADO"
        )
        print(
            "FASE 10 - COACH LEARNING LOOP: CONCLUÍDA"
        )
        raise SystemExit(0)

    print(
        "END-TO-END LEARNING LOOP V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
