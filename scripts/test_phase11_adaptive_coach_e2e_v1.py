from __future__ import annotations

import ast
import json
import sys
import tempfile
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coach_intelligence.services.adaptive_coach_intelligence_service import (
    AdaptiveCoachIntelligenceService,
)


class Level(IntEnum):
    NOT_EVALUATED = 0
    BEGINNER = 1
    DEVELOPING = 2
    COMPETENT = 3
    ADVANCED = 4
    MASTERED = 5


@dataclass(frozen=True)
class Skill:
    id: str
    title: str


@dataclass(frozen=True)
class Assessment:
    skill: Skill
    score: float
    level: Level
    confidence: float
    evidence_metric_ids: tuple[str, ...]
    limitations: tuple[str, ...]


class FakeRepository:
    def __init__(
        self,
        root: Path,
    ) -> None:
        self.root = root

    def get_player_directory(
        self,
        *,
        puuid: str,
    ) -> Path:
        path = self.root / puuid
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
        return path

    @staticmethod
    def _read_json(
        *,
        path: Path,
    ):
        if not path.exists():
            return None

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def _write_json(
        *,
        path: Path,
        data,
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def cycle(
    *,
    cycle_id: str,
    skill_id: str,
    task_id: str,
    task_title: str,
    result: str,
):
    return {
        "cycle_id": cycle_id,
        "mission": {
            "task": {
                "id": task_id,
                "skill_id": skill_id,
                "title": task_title,
            }
        },
        "evaluation": {
            "result": result,
            "confidence": "MODERATE",
            "confidence_score": 70.0,
        },
    }


def assessments(
    *,
    leveling_score: float,
    leveling_level: Level,
    board_score: float = 48.0,
    consistency_score: float = 30.0,
):
    return (
        Assessment(
            Skill(
                "leveling",
                "Leveling",
            ),
            leveling_score,
            leveling_level,
            90.0,
            (
                "average_level",
            ),
            (),
        ),
        Assessment(
            Skill(
                "consistency",
                "Consistency",
            ),
            consistency_score,
            Level.DEVELOPING,
            80.0,
            (
                "placement_standard_deviation",
            ),
            (),
        ),
        Assessment(
            Skill(
                "board_pressure",
                "Board Pressure",
            ),
            board_score,
            Level.COMPETENT,
            90.0,
            (
                "average_damage_to_players",
            ),
            (),
        ),
        Assessment(
            Skill(
                "economy",
                "Economy",
            ),
            0.0,
            Level.NOT_EVALUATED,
            0.0,
            (),
            (
                "Sem evidência direta suficiente.",
            ),
        ),
    )


def memory(
    *,
    trend: str,
    anti_loop: str,
    progression: str,
    current_task_id: str,
    current_difficulty: str,
    latest_result: str,
    cycles_total: int,
    conclusive_cycles: int,
):
    return {
        "skills": {
            "leveling": {
                "cycles_total": cycles_total,
                "conclusive_cycles": (
                    conclusive_cycles
                ),
                "trend": trend,
                "trend_confidence": (
                    "MODERATE"
                    if conclusive_cycles >= 2
                    else "LOW"
                ),
                "latest_result": latest_result,
                "current_task_id": current_task_id,
                "current_difficulty": (
                    current_difficulty
                ),
                "anti_loop_action": anti_loop,
                "task_progression": progression,
            }
        }
    }


def build_case(
    *,
    repo,
    puuid: str,
    score: float,
    level: Level,
    mem: dict,
    history: list[dict],
    task_id: str,
):
    return AdaptiveCoachIntelligenceService.build(
        puuid=puuid,
        assessments=assessments(
            leveling_score=score,
            leveling_level=level,
        ),
        pedagogical_memory=mem,
        training_history=history,
        priority_skill_id="leveling",
        current_task_id=task_id,
        player_repository=repo,
        persist_profile=True,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        repo = FakeRepository(
            Path(temp)
        )

        # CASE 1: Current-like state.
        current = build_case(
            repo=repo,
            puuid="current",
            score=15.22,
            level=Level.BEGINNER,
            mem=memory(
                trend="INSUFFICIENT_HISTORY",
                anti_loop="CONTINUE",
                progression="HOLD",
                current_task_id=(
                    "plan_level_before_spending"
                ),
                current_difficulty="FOUNDATION",
                latest_result="NEGATIVE",
                cycles_total=1,
                conclusive_cycles=1,
            ),
            history=[
                cycle(
                    cycle_id="c1",
                    skill_id="leveling",
                    task_id=(
                        "balance_level_and_stability"
                    ),
                    task_title=(
                        "Equilibrar nível e estabilidade"
                    ),
                    result="NEGATIVE",
                )
            ],
            task_id="plan_level_before_spending",
        )

        # CASE 2: Improving + advance.
        improving = build_case(
            repo=repo,
            puuid="improving",
            score=41.0,
            level=Level.COMPETENT,
            mem=memory(
                trend="IMPROVING",
                anti_loop="CONTINUE",
                progression="ADVANCE_CANDIDATE",
                current_task_id=(
                    "plan_level_before_spending"
                ),
                current_difficulty="FOUNDATION",
                latest_result="POSITIVE",
                cycles_total=2,
                conclusive_cycles=2,
            ),
            history=[
                cycle(
                    cycle_id="i2",
                    skill_id="leveling",
                    task_id=(
                        "plan_level_before_spending"
                    ),
                    task_title=(
                        "Planejar o próximo nível"
                    ),
                    result="POSITIVE",
                ),
                cycle(
                    cycle_id="i1",
                    skill_id="leveling",
                    task_id=(
                        "balance_level_and_stability"
                    ),
                    task_title=(
                        "Equilibrar nível e estabilidade"
                    ),
                    result="NEGATIVE",
                ),
            ],
            task_id="plan_level_before_spending",
        )

        # CASE 3: Stable.
        stable = build_case(
            repo=repo,
            puuid="stable",
            score=52.0,
            level=Level.COMPETENT,
            mem=memory(
                trend="STABLE",
                anti_loop="ROTATE_TASK",
                progression="ROTATE",
                current_task_id=(
                    "balance_level_and_stability"
                ),
                current_difficulty="INTERMEDIATE",
                latest_result="STABLE",
                cycles_total=2,
                conclusive_cycles=2,
            ),
            history=[
                cycle(
                    cycle_id="s2",
                    skill_id="leveling",
                    task_id=(
                        "balance_level_and_stability"
                    ),
                    task_title=(
                        "Equilibrar nível e estabilidade"
                    ),
                    result="STABLE",
                ),
                cycle(
                    cycle_id="s1",
                    skill_id="leveling",
                    task_id=(
                        "balance_level_and_stability"
                    ),
                    task_title=(
                        "Equilibrar nível e estabilidade"
                    ),
                    result="STABLE",
                ),
            ],
            task_id="balance_level_and_stability",
        )

        # CASE 4: Reassess.
        reassess = build_case(
            repo=repo,
            puuid="reassess",
            score=20.0,
            level=Level.BEGINNER,
            mem=memory(
                trend="REGRESSING",
                anti_loop="REASSESS",
                progression="PAUSE_AND_REASSESS",
                current_task_id=(
                    "balance_level_and_stability"
                ),
                current_difficulty="INTERMEDIATE",
                latest_result="NEGATIVE",
                cycles_total=2,
                conclusive_cycles=2,
            ),
            history=[
                cycle(
                    cycle_id="r2",
                    skill_id="leveling",
                    task_id=(
                        "balance_level_and_stability"
                    ),
                    task_title=(
                        "Equilibrar nível e estabilidade"
                    ),
                    result="NEGATIVE",
                ),
                cycle(
                    cycle_id="r1",
                    skill_id="leveling",
                    task_id=(
                        "plan_level_before_spending"
                    ),
                    task_title=(
                        "Planejar o próximo nível"
                    ),
                    result="NEGATIVE",
                ),
            ],
            task_id="balance_level_and_stability",
        )

        # CASE 5: Cooldown.
        cooldown = build_case(
            repo=repo,
            puuid="cooldown",
            score=18.0,
            level=Level.BEGINNER,
            mem=memory(
                trend="REGRESSING",
                anti_loop="COOLDOWN_SKILL",
                progression="PAUSE_AND_REASSESS",
                current_task_id=(
                    "avoid_unplanned_rerolls"
                ),
                current_difficulty="ADVANCED",
                latest_result="NEGATIVE",
                cycles_total=3,
                conclusive_cycles=3,
            ),
            history=[
                cycle(
                    cycle_id="d3",
                    skill_id="leveling",
                    task_id=(
                        "avoid_unplanned_rerolls"
                    ),
                    task_title=(
                        "Evitar rerolls sem planejamento"
                    ),
                    result="NEGATIVE",
                ),
                cycle(
                    cycle_id="d2",
                    skill_id="leveling",
                    task_id=(
                        "balance_level_and_stability"
                    ),
                    task_title=(
                        "Equilibrar nível e estabilidade"
                    ),
                    result="NEGATIVE",
                ),
                cycle(
                    cycle_id="d1",
                    skill_id="leveling",
                    task_id=(
                        "plan_level_before_spending"
                    ),
                    task_title=(
                        "Planejar o próximo nível"
                    ),
                    result="NEGATIVE",
                ),
            ],
            task_id="avoid_unplanned_rerolls",
        )

        # CASE 6: effectiveness overrides generic maintain.
        low_effectiveness = build_case(
            repo=repo,
            puuid="low_effectiveness",
            score=65.0,
            level=Level.ADVANCED,
            mem=memory(
                trend="INSUFFICIENT_HISTORY",
                anti_loop="CONTINUE",
                progression="HOLD",
                current_task_id=(
                    "plan_level_before_spending"
                ),
                current_difficulty="INTERMEDIATE",
                latest_result="NEGATIVE",
                cycles_total=2,
                conclusive_cycles=2,
            ),
            history=[
                cycle(
                    cycle_id="e2",
                    skill_id="leveling",
                    task_id=(
                        "plan_level_before_spending"
                    ),
                    task_title=(
                        "Planejar o próximo nível"
                    ),
                    result="NEGATIVE",
                ),
                cycle(
                    cycle_id="e1",
                    skill_id="leveling",
                    task_id=(
                        "plan_level_before_spending"
                    ),
                    task_title=(
                        "Planejar o próximo nível"
                    ),
                    result="NEGATIVE",
                ),
            ],
            task_id="plan_level_before_spending",
        )

        current_profile_file = (
            repo.get_player_directory(
                puuid="current"
            )
            / "learning"
            / "learning_profile.json"
        )

        persisted_current = repo._read_json(
            path=current_profile_file
        )

    # Static API/UI contract.
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

    checks = [
        # Current state.
        (
            "Current-like mantém Leveling",
            current["strategy"][
                "priority_skill_id"
            ] == "leveling",
        ),
        (
            "Current-like usa BUILD_FOUNDATION",
            current["strategy"][
                "strategy"
            ] == "BUILD_FOUNDATION",
        ),
        (
            "Current-like mantém score recebido",
            current["strategy"][
                "current_score"
            ] == 15.22,
        ),
        (
            "Current-like preserva FOUNDATION",
            current["strategy"][
                "current_difficulty"
            ] == "FOUNDATION",
        ),
        (
            "Current-like explicação é determinística",
            current["explanation"][
                "source"
            ] == "deterministic",
        ),

        # Improving.
        (
            "IMPROVING + ADVANCE vira CHALLENGE",
            improving["strategy"][
                "strategy"
            ] == "CHALLENGE",
        ),
        (
            "CHALLENGE não troca Skill",
            improving["strategy"][
                "priority_skill_id"
            ] == "leveling",
        ),

        # Stable.
        (
            "STABLE vira CONSOLIDATE",
            stable["strategy"][
                "strategy"
            ] == "CONSOLIDATE",
        ),

        # Reassess/cooldown.
        (
            "REASSESS vira CHANGE_APPROACH",
            reassess["strategy"][
                "strategy"
            ] == "CHANGE_APPROACH",
        ),
        (
            "COOLDOWN vira CHANGE_APPROACH",
            cooldown["strategy"][
                "strategy"
            ] == "CHANGE_APPROACH",
        ),
        (
            "COOLDOWN mantém prioridade recebida",
            cooldown["strategy"][
                "priority_skill_id"
            ] == "leveling",
        ),

        # Task effectiveness.
        (
            "2 NEGATIVE da mesma task = LOW effectiveness",
            low_effectiveness[
                "training_effectiveness"
            ][0][
                "effectiveness"
            ]
            == "LOW_OBSERVED_EFFECTIVENESS",
        ),
        (
            "LOW effectiveness força CHANGE_APPROACH",
            low_effectiveness["strategy"][
                "strategy"
            ] == "CHANGE_APPROACH",
        ),

        # Profile and persistence.
        (
            "Profile inclui 4 Skills",
            len(
                current["profile"].get(
                    "skills",
                    {}
                )
            )
            == 4,
        ),
        (
            "Economy permanece NOT_EVALUATED",
            current["profile"]["skills"][
                "economy"
            ][
                "level"
            ]
            == "NOT_EVALUATED",
        ),
        (
            "Economy não recebe score inventado",
            current["profile"]["skills"][
                "economy"
            ][
                "score"
            ]
            is None,
        ),
        (
            "Perfil foi persistido",
            isinstance(
                persisted_current,
                dict,
            ),
        ),
        (
            "Persistência guarda prioridade correta",
            persisted_current[
                "current_priority_skill_id"
            ]
            == "leveling",
        ),

        # Score consistency contract.
        (
            "Score do strategy = score do profile",
            current["strategy"][
                "current_score"
            ]
            == current["profile"][
                "skills"
            ][
                "leveling"
            ][
                "score"
            ],
        ),
        (
            "Score do payload não é recalculado pela explicação",
            "current_score" not in current[
                "explanation"
            ],
        ),

        # Explanation safety.
        (
            "Explicação declara não causalidade",
            any(
                "não prova" in item
                for item in current[
                    "explanation"
                ][
                    "limitations"
                ]
            ),
        ),
        (
            "Explicação preserva Learning Priority",
            any(
                "Learning Priority" in item
                for item in current[
                    "explanation"
                ][
                    "limitations"
                ]
            ),
        ),

        # API integration.
        (
            "API publica adaptive_coach",
            'comparison_data["adaptive_coach"]'
            in route,
        ),
        (
            "API usa SkillMappingService oficial",
            "SkillMappingService.assess"
            in route,
        ),
        (
            "API usa mesma Performance para assessments",
            "performance=analysis.performance"
            in route,
        ),
        (
            "API passa current task real",
            "current_task_id=pipeline.mission.task.id"
            in route,
        ),

        # Contract.
        (
            "Contrato possui BenchmarkAdaptiveCoach",
            "class BenchmarkAdaptiveCoach"
            in contract,
        ),
        (
            "Response expõe adaptive_coach",
            "adaptive_coach: BenchmarkAdaptiveCoach"
            in contract,
        ),

        # UI.
        (
            "UI renderiza adaptive_coach",
            'comparison.get("adaptive_coach")'
            in page,
        ),
        (
            "UI mostra estratégia",
            'title="Estratégia"'
            in page,
        ),
        (
            "UI traduz tendência",
            "_LEARNING_TREND_LABELS.get"
            in page,
        ),
        (
            "UI possui explicabilidade",
            "Por que o coach escolheu esta estratégia?"
            in page,
        ),

        # Architecture invariants.
        (
            "Nenhum cenário trocou a Skill",
            all(
                item["strategy"][
                    "priority_skill_id"
                ]
                == "leveling"
                for item in (
                    current,
                    improving,
                    stable,
                    reassess,
                    cooldown,
                    low_effectiveness,
                )
            ),
        ),
        (
            "Adaptive service entrega as 6 seções",
            all(
                key in current
                for key in (
                    "strategy",
                    "explanation",
                    "profile",
                    "evolution",
                    "cross_skill_insights",
                    "training_effectiveness",
                )
            ),
        ),
    ]

    print("=" * 82)
    print(
        "TFT INSIGHT - FASE 11.8 - END-TO-END ADAPTIVE COACH V1"
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
    print("CENÁRIOS")
    print("-" * 82)
    print(
        "Histórico insuficiente -> "
        f"{current['strategy']['strategy']}"
    )
    print(
        "Melhorando + avanço -> "
        f"{improving['strategy']['strategy']}"
    )
    print(
        "Estável -> "
        f"{stable['strategy']['strategy']}"
    )
    print(
        "Reassess -> "
        f"{reassess['strategy']['strategy']}"
    )
    print(
        "Cooldown -> "
        f"{cooldown['strategy']['strategy']}"
    )
    print(
        "Task com baixa efetividade -> "
        f"{low_effectiveness['strategy']['strategy']}"
    )

    print()
    print("-" * 82)
    print("CONSISTÊNCIA DE SCORE")
    print("-" * 82)
    print(
        "Strategy score : "
        f"{current['strategy']['current_score']}"
    )
    print(
        "Profile score  : "
        f"{current['profile']['skills']['leveling']['score']}"
    )
    print(
        "Regra          : a explicação não recalcula score."
    )

    print()
    print("=" * 82)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "END-TO-END ADAPTIVE COACH V1: VALIDADO"
        )
        print(
            "FASE 11 - ADAPTIVE COACH INTELLIGENCE: CONCLUÍDA"
        )
        raise SystemExit(0)

    print(
        "END-TO-END ADAPTIVE COACH V1: AJUSTE NECESSÁRIO"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
