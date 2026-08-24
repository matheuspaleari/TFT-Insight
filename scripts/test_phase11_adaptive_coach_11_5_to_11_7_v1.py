from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coach_intelligence.services.adaptive_coach_intelligence_service import (
    AdaptiveCoachIntelligenceService,
)
from src.coach_intelligence.services.adaptive_coaching_strategy_engine import (
    AdaptiveCoachingStrategyEngine,
)
from src.coach_intelligence.services.coach_explanation_engine import (
    CoachExplanationEngine,
)


def foundation(
    *,
    level="BEGINNER",
    score=20.0,
    trend="INSUFFICIENT_HISTORY",
    difficulty="FOUNDATION",
    anti_loop="CONTINUE",
    progression="HOLD",
    effectiveness="INSUFFICIENT_HISTORY",
):
    return {
        "profile": {
            "skills": {
                "leveling": {
                    "skill_id": "leveling",
                    "skill_name": "Leveling",
                    "level": level,
                    "score": score,
                    "trend": trend,
                    "current_difficulty": difficulty,
                    "anti_loop_action": anti_loop,
                    "task_progression": progression,
                }
            }
        },
        "evolution": [],
        "cross_skill_insights": [],
        "training_effectiveness": [
            {
                "skill_id": "leveling",
                "task_id": "task-a",
                "effectiveness": effectiveness,
            }
        ],
    }


def decide(**kwargs):
    return AdaptiveCoachingStrategyEngine.decide(
        foundation=foundation(**kwargs),
        priority_skill_id="leveling",
        current_task_id="task-a",
    )


def main() -> None:
    build = decide()
    consolidate = decide(
        level="COMPETENT",
        score=55.0,
        trend="STABLE",
        difficulty="INTERMEDIATE",
    )
    challenge = decide(
        level="DEVELOPING",
        score=38.0,
        trend="IMPROVING",
        difficulty="FOUNDATION",
        progression="ADVANCE_CANDIDATE",
    )
    change_low = decide(
        level="DEVELOPING",
        score=32.0,
        trend="REGRESSING",
        difficulty="INTERMEDIATE",
        effectiveness="LOW_OBSERVED_EFFECTIVENESS",
    )
    change_guard = decide(
        level="DEVELOPING",
        score=32.0,
        trend="REGRESSING",
        difficulty="FOUNDATION",
        anti_loop="REASSESS",
        progression="PAUSE_AND_REASSESS",
    )
    maintain = decide(
        level="ADVANCED",
        score=78.0,
        trend="INSUFFICIENT_HISTORY",
        difficulty=None,
    )

    explanation = CoachExplanationEngine.explain(
        strategy=challenge,
        foundation=foundation(
            level="DEVELOPING",
            score=38.0,
            trend="IMPROVING",
            difficulty="FOUNDATION",
            progression="ADVANCE_CANDIDATE",
        ),
    )

    route_path = PROJECT_ROOT / "src/integration_engine/api/routes/benchmark.py"
    contract_path = PROJECT_ROOT / "src/integration_engine/contracts/benchmark.py"
    page_path = PROJECT_ROOT / "partner_platform/pages/benchmark_page.py"

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
        ("11.5 Foundation -> BUILD_FOUNDATION", build.strategy == "BUILD_FOUNDATION"),
        ("11.5 Foundation usa confiança conservadora", build.confidence == "LOW"),
        ("11.5 STABLE -> CONSOLIDATE", consolidate.strategy == "CONSOLIDATE"),
        ("11.5 IMPROVING + ADVANCE -> CHALLENGE", challenge.strategy == "CHALLENGE"),
        ("11.5 LOW effectiveness -> CHANGE_APPROACH", change_low.strategy == "CHANGE_APPROACH"),
        ("11.5 REASSESS -> CHANGE_APPROACH", change_guard.strategy == "CHANGE_APPROACH"),
        ("11.5 REASSESS não troca Skill", change_guard.priority_skill_id == "leveling"),
        ("11.5 estratégia mantém safeguards", len(challenge.safeguards) == 3),
        ("11.5 não usa cross-skill para trocar prioridade", challenge.priority_skill_id == "leveling"),
        ("11.5 task effectiveness é preservada", change_low.task_effectiveness == "LOW_OBSERVED_EFFECTIVENESS"),
        ("11.6 explicação tem título", bool(explanation.title)),
        ("11.6 explicação cita Skill", "Leveling" in explanation.title),
        ("11.6 explicação tem próximo passo", bool(explanation.next_step)),
        ("11.6 explicação tem evidências", len(explanation.evidence) >= 4),
        ("11.6 explicação tem limitações", len(explanation.limitations) >= 2),
        ("11.6 explicação é determinística", explanation.source == "deterministic"),
        ("11.6 não afirma causalidade", any("não prova" in item for item in explanation.limitations)),
        ("11.6 mantém Learning Priority soberano", any("Learning Priority" in item for item in explanation.limitations)),
        ("11.7 rota importa AdaptiveCoachIntelligenceService", "AdaptiveCoachIntelligenceService" in route),
        ("11.7 rota gera SkillAssessments oficiais", "SkillMappingService.assess" in route),
        ("11.7 rota publica adaptive_coach", 'comparison_data["adaptive_coach"]' in route),
        ("11.7 contrato possui BenchmarkAdaptiveStrategy", "class BenchmarkAdaptiveStrategy" in contract),
        ("11.7 contrato possui BenchmarkCoachExplanation", "class BenchmarkCoachExplanation" in contract),
        ("11.7 contrato possui BenchmarkAdaptiveCoach", "class BenchmarkAdaptiveCoach" in contract),
        ("11.7 response expõe adaptive_coach", "adaptive_coach: BenchmarkAdaptiveCoach" in contract),
        ("11.7 UI possui renderer adaptativo", "def _render_adaptive_coach(" in page),
        ("11.7 UI mostra Estratégia", 'title="Estratégia"' in page),
        ("11.7 UI mostra Leitura adaptativa", 'eyebrow="Leitura adaptativa"' in page),
        ("11.7 UI mostra explicabilidade", "Por que o coach escolheu esta estratégia?" in page),
        ("11.7 UI renderiza adaptive_coach", 'comparison.get("adaptive_coach")' in page),
    ]

    print("=" * 82)
    print("TFT INSIGHT - FASE 11.5 + 11.6 + 11.7 - VALIDATION V1")
    print("=" * 82)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        start=1,
    ):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("-" * 82)
    print("EXEMPLOS DE ESTRATÉGIA")
    print("-" * 82)
    print(f"Fundamentos : {build.strategy}")
    print(f"Estável     : {consolidate.strategy}")
    print(f"Melhorando  : {challenge.strategy}")
    print(f"Baixa efet. : {change_low.strategy}")
    print(f"Reassess    : {change_guard.strategy}")

    print()
    print("=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("FASE 11.5-11.7 ADAPTIVE COACH V1: VALIDADO")
        raise SystemExit(0)

    print("FASE 11.5-11.7 ADAPTIVE COACH V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
