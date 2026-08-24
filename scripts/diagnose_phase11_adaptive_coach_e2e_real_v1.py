from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(
    PROJECT_ROOT / ".env"
)

from src.coach_intelligence.services.adaptive_coach_intelligence_service import (
    AdaptiveCoachIntelligenceService,
)
from src.learning import SkillMappingService
from src.riot_client import RiotClient
from src.services import PlayerAnalysisService
from src.storage import PlayerRepository


def main() -> None:
    print("=" * 82)
    print(
        "TFT INSIGHT - FASE 11.8 - DIAGNÓSTICO END-TO-END REAL"
    )
    print("=" * 82)

    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    benchmark_id = input(
        "Benchmark ID [advanced]: "
    ).strip() or "advanced"

    match_count = int(
        input(
            "Quantidade de partidas [30]: "
        ).strip()
        or "30"
    )

    priority = input(
        "Prioridade atual [leveling]: "
    ).strip() or "leveling"

    riot = RiotClient()
    account = riot.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    puuid = str(
        account.get(
            "puuid",
            "",
        )
    )

    if not puuid:
        raise RuntimeError(
            "PUUID não retornado pela Riot."
        )

    analysis = PlayerAnalysisService().analyze(
        game_name=game_name,
        tag_line=tag_line,
        benchmark_id=benchmark_id,
        match_count=match_count,
        use_cache=True,
    )

    assessments = SkillMappingService.assess(
        performance=analysis.performance,
    )

    repo = PlayerRepository()

    memory = repo.load_pedagogical_memory(
        puuid=puuid
    )

    history = repo.list_training_cycles(
        puuid=puuid
    )

    current = repo.load_training_mission(
        puuid=puuid
    )

    result = AdaptiveCoachIntelligenceService.build(
        puuid=puuid,
        assessments=assessments,
        pedagogical_memory=memory,
        training_history=history,
        priority_skill_id=priority,
        current_task_id=(
            current.task.id
            if current is not None
            else None
        ),
        player_repository=repo,
        persist_profile=True,
    )

    strategy = result[
        "strategy"
    ]

    profile_skill = (
        result[
            "profile"
        ][
            "skills"
        ].get(
            priority,
            {},
        )
    )

    print()
    print("=" * 82)
    print("END-TO-END REAL")
    print("=" * 82)
    print(
        f"Partidas da análise    : {match_count}"
    )
    print(
        f"Prioridade             : {priority}"
    )
    print(
        f"Score no profile       : {profile_skill.get('score')}"
    )
    print(
        f"Score na strategy      : {strategy.get('current_score')}"
    )
    print(
        f"Nível                  : {strategy.get('current_level')}"
    )
    print(
        f"Tendência              : {strategy.get('training_trend')}"
    )
    print(
        f"Estratégia             : {strategy.get('strategy')}"
    )
    print(
        f"Confiança              : {strategy.get('confidence')}"
    )
    print(
        f"Task atual             : {strategy.get('current_task_id') or '-'}"
    )
    print(
        f"Dificuldade            : {strategy.get('current_difficulty') or '-'}"
    )
    print(
        f"Efetividade da task    : {strategy.get('task_effectiveness')}"
    )
    print(
        f"Anti-Loop              : {strategy.get('anti_loop_action')}"
    )

    print()
    print("VALIDAÇÃO DE SCORE")
    profile_score = profile_skill.get(
        "score"
    )
    strategy_score = strategy.get(
        "current_score"
    )

    print(
        "Profile == Strategy    : "
        f"{'SIM' if profile_score == strategy_score else 'NÃO'}"
    )

    print()
    print("EXPLICAÇÃO")
    print(
        result[
            "explanation"
        ][
            "summary"
        ]
    )

    print()
    print("=" * 82)
    print("PIPELINE")
    print("=" * 82)
    print(
        "Performance -> SkillAssessment -> Learning Profile -> Evolution -> "
        "Cross-Skill -> Training Effectiveness -> Adaptive Strategy -> "
        "Explanation"
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "Use a mesma quantidade de partidas da UI ao comparar scores."
    )
    print(
        "O Adaptive Coach recebe a Skill prioritária pronta e não escolhe "
        "outra Skill."
    )
    print(
        "A explicação não recalcula o score e não atribui causalidade."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'END-TO-END REAL' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
