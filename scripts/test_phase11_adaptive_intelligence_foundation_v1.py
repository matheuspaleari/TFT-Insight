from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coach_intelligence.services.adaptive_intelligence_foundation import (
    AdaptiveIntelligenceFoundation,
)
from src.coach_intelligence.services.cross_skill_relationship_engine import (
    CrossSkillRelationshipEngine,
)
from src.coach_intelligence.services.player_learning_profile_service import (
    PlayerLearningProfileService,
)
from src.coach_intelligence.services.skill_evolution_engine import (
    SkillEvolutionEngine,
)
from src.coach_intelligence.services.training_effectiveness_engine import (
    TrainingEffectivenessEngine,
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
    cycle_id,
    skill_id,
    task_id,
    result,
):
    return {
        "cycle_id": cycle_id,
        "mission": {
            "task": {
                "id": task_id,
                "skill_id": skill_id,
                "title": task_id,
            }
        },
        "evaluation": {
            "result": result,
        },
    }


def main() -> None:
    assessments = (
        Assessment(
            Skill(
                "leveling",
                "Leveling",
            ),
            32.3,
            Level.DEVELOPING,
            90.0,
            ("average_level",),
            (),
        ),
        Assessment(
            Skill(
                "board_pressure",
                "Board Pressure",
            ),
            28.0,
            Level.DEVELOPING,
            90.0,
            (
                "average_damage_to_players",
                "average_players_eliminated",
            ),
            (),
        ),
        Assessment(
            Skill(
                "consistency",
                "Consistency",
            ),
            82.0,
            Level.MASTERED,
            80.0,
            ("consistency",),
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
            ("sem evidência direta",),
        ),
    )

    memory = {
        "skills": {
            "leveling": {
                "cycles_total": 1,
                "conclusive_cycles": 1,
                "trend": "INSUFFICIENT_HISTORY",
                "trend_confidence": "LOW",
                "latest_result": "NEGATIVE",
                "current_task_id": "plan_level_before_spending",
                "current_difficulty": "FOUNDATION",
                "anti_loop_action": "CONTINUE",
                "task_progression": "HOLD",
            },
            "consistency": {
                "cycles_total": 1,
                "conclusive_cycles": 0,
                "trend": "INSUFFICIENT_HISTORY",
                "trend_confidence": "LOW",
                "latest_result": "INCONCLUSIVE",
                "anti_loop_action": "CONTINUE",
                "task_progression": "HOLD",
            },
        }
    }

    profile = (
        PlayerLearningProfileService.build(
            assessments=assessments,
            pedagogical_memory=memory,
            current_priority_skill_id="leveling",
        )
    )

    previous = profile.to_dict()
    previous["skills"]["leveling"]["score"] = 25.0
    previous["skills"]["leveling"]["level"] = "DEVELOPING"

    evolution = (
        SkillEvolutionEngine.compare(
            current_profile=profile,
            previous_profile=previous,
        )
    )

    cross = (
        CrossSkillRelationshipEngine.analyze(
            profile=profile
        )
    )

    history = [
        cycle(
            "1",
            "leveling",
            "plan_level_before_spending",
            "POSITIVE",
        ),
        cycle(
            "2",
            "leveling",
            "plan_level_before_spending",
            "POSITIVE",
        ),
        cycle(
            "3",
            "leveling",
            "balance_level_and_stability",
            "NEGATIVE",
        ),
        cycle(
            "4",
            "leveling",
            "balance_level_and_stability",
            "NEGATIVE",
        ),
        cycle(
            "5",
            "consistency",
            "define_simple_game_plan",
            "INCONCLUSIVE",
        ),
    ]

    effectiveness = (
        TrainingEffectivenessEngine.evaluate(
            training_history=history
        )
    )

    leveling = profile.get_skill(
        "leveling"
    )
    economy = profile.get_skill(
        "economy"
    )
    leveling_evolution = next(
        item
        for item in evolution
        if item.skill_id == "leveling"
    )
    consistency_relation = next(
        (
            item
            for item in cross
            if item.relationship_id
            == "consistency_to_board_pressure"
        ),
        None,
    )
    promising = next(
        item
        for item in effectiveness
        if item.task_id
        == "plan_level_before_spending"
    )
    low = next(
        item
        for item in effectiveness
        if item.task_id
        == "balance_level_and_stability"
    )

    with tempfile.TemporaryDirectory() as temp:
        repo = FakeRepository(
            Path(temp)
        )
        first = AdaptiveIntelligenceFoundation.build(
            puuid="player",
            assessments=assessments,
            pedagogical_memory=memory,
            training_history=history,
            current_priority_skill_id="leveling",
            player_repository=repo,
            persist=True,
        )
        second = AdaptiveIntelligenceFoundation.build(
            puuid="player",
            assessments=assessments,
            pedagogical_memory=memory,
            training_history=history,
            current_priority_skill_id="leveling",
            player_repository=repo,
            persist=True,
        )
        profile_file = (
            repo.get_player_directory(
                puuid="player"
            )
            / "learning"
            / "learning_profile.json"
        )
        persisted = repo._read_json(
            path=profile_file
        )
        profile_file_persisted = (
            profile_file.exists()
            and isinstance(
                persisted,
                dict,
            )
        )

    checks = [
        ("11.1 cria perfil", len(profile.skills) == 4),
        ("11.1 prioridade fica IN_TRAINING", leveling.state == "IN_TRAINING"),
        ("11.1 preserva FOUNDATION", leveling.current_difficulty == "FOUNDATION"),
        ("11.1 preserva último NEGATIVE", leveling.latest_training_result == "NEGATIVE"),
        ("11.1 Leveling usa nome semântico", leveling.level == "DEVELOPING"),
        ("11.1 não inventa score de Economy", economy.score is None),
        ("11.1 Economy permanece NOT_EVALUATED", economy.level == "NOT_EVALUATED"),
        ("11.1 Economy não vira oportunidade artificial", economy.state == "OBSERVED"),
        ("11.2 calcula delta técnico", round(leveling_evolution.score_delta, 2) == 7.30),
        ("11.2 delta positivo classifica IMPROVING", leveling_evolution.direction == "IMPROVING"),
        ("11.2 ausência de snapshot é conservadora", all(item.direction in {"IMPROVING", "STABLE", "REGRESSING", "INSUFFICIENT_HISTORY"} for item in evolution)),
        ("11.3 encontra relação consistency/board", consistency_relation is not None),
        ("11.3 relação não afirma causalidade", "não prova" in consistency_relation.limitation),
        ("11.3 ignora Economy sem score", all(item.source_skill_id != "economy" and item.target_skill_id != "economy" for item in cross)),
        ("11.4 dois POSITIVE = PROMISING", promising.effectiveness == "PROMISING"),
        ("11.4 dois NEGATIVE = LOW", low.effectiveness == "LOW_OBSERVED_EFFECTIVENESS"),
        ("11.4 histórico de 1 ciclo é insuficiente", next(item for item in effectiveness if item.skill_id == "consistency").effectiveness == "INSUFFICIENT_HISTORY"),
        ("11.4 não afirma causalidade", "não atribui causalidade" in promising.rationale),
        ("Foundation integra 11.1", "profile" in first),
        ("Foundation integra 11.2", "evolution" in first),
        ("Foundation integra 11.3", "cross_skill_insights" in first),
        ("Foundation integra 11.4", "training_effectiveness" in first),
        ("Perfil é persistido", profile_file_persisted),
        ("Segundo snapshot preserva histórico", len(persisted.get("snapshots", [])) == 1),
        ("Persistência não altera memória da Fase 10", persisted.get("current_priority_skill_id") == "leveling"),
        ("Resultado é serializável", isinstance(second["profile"]["skills"], dict)),
    ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 11.1 A 11.4 - FOUNDATION V1")
    print("=" * 82)

    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("-" * 82)
    print("PERFIL LEVELING")
    print("-" * 82)
    print(f"Estado       : {leveling.state}")
    print(f"Score        : {leveling.score}")
    print(f"Nível        : {leveling.level}")
    print(f"Tendência    : {leveling.trend}")
    print(f"Dificuldade  : {leveling.current_difficulty}")

    print()
    print("-" * 82)
    print("EFETIVIDADE SIMULADA")
    print("-" * 82)
    print(
        "plan_level_before_spending: "
        f"{promising.effectiveness}"
    )
    print(
        "balance_level_and_stability: "
        f"{low.effectiveness}"
    )

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("FASE 11.1-11.4 FOUNDATION V1: VALIDADO")
        raise SystemExit(0)

    print("FASE 11.1-11.4 FOUNDATION V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
