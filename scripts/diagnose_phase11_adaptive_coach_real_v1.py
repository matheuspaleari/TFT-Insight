from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.coach_intelligence.services.adaptive_coach_intelligence_service import (
    AdaptiveCoachIntelligenceService,
)
from src.learning import SkillMappingService
from src.riot_client import RiotClient
from src.services import PlayerAnalysisService
from src.storage import PlayerRepository


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - FASE 11.5/11.6/11.7 - DIAGNÓSTICO REAL")
    print("=" * 82)

    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()
    benchmark_id = input(
        "Benchmark ID [advanced]: "
    ).strip() or "advanced"
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
        match_count=30,
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

    current_task_id = (
        current.task.id
        if current is not None
        else None
    )

    result = AdaptiveCoachIntelligenceService.build(
        puuid=puuid,
        assessments=assessments,
        pedagogical_memory=memory,
        training_history=history,
        priority_skill_id=priority,
        current_task_id=current_task_id,
        player_repository=repo,
        persist_profile=True,
    )

    strategy = result[
        "strategy"
    ]
    explanation = result[
        "explanation"
    ]

    print()
    print("=" * 82)
    print("ADAPTIVE COACH STRATEGY")
    print("=" * 82)
    print(
        f"Prioridade recebida  : {strategy['priority_skill_id']}"
    )
    print(
        f"Estratégia           : {strategy['strategy']}"
    )
    print(
        f"Confiança            : {strategy['confidence']}"
    )
    print(
        f"Nível atual          : {strategy['current_level']}"
    )
    print(
        f"Score atual          : {strategy['current_score'] if strategy['current_score'] is not None else '-'}"
    )
    print(
        f"Tendência            : {strategy['training_trend']}"
    )
    print(
        f"Task atual           : {strategy['current_task_id'] or '-'}"
    )
    print(
        f"Dificuldade          : {strategy['current_difficulty'] or '-'}"
    )
    print(
        f"Efetividade task     : {strategy['task_effectiveness']}"
    )
    print(
        f"Anti-Loop            : {strategy['anti_loop_action']}"
    )

    print()
    print("MOTIVO")
    print(
        strategy[
            "rationale"
        ]
    )

    print()
    print("=" * 82)
    print("COACH EXPLANATION")
    print("=" * 82)
    print(
        f"Título: {explanation['title']}"
    )
    print()
    print(
        explanation[
            "summary"
        ]
    )
    print()
    print(
        "Próximo passo:"
    )
    print(
        explanation[
            "next_step"
        ]
    )

    print()
    print("EVIDÊNCIAS")
    for item in explanation[
        "evidence"
    ]:
        print(
            f"- {item}"
        )

    print()
    print("LIMITAÇÕES")
    for item in explanation[
        "limitations"
    ]:
        print(
            f"- {item}"
        )

    print()
    print("=" * 82)
    print("INTELLIGENCE PAYLOAD")
    print("=" * 82)
    print(
        f"Skills no perfil     : {len(result['profile'].get('skills', {}))}"
    )
    print(
        f"Evoluções            : {len(result['evolution'])}"
    )
    print(
        f"Cross-Skill signals  : {len(result['cross_skill_insights'])}"
    )
    print(
        f"Tasks avaliadas      : {len(result['training_effectiveness'])}"
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "A estratégia recebeu a prioridade pronta e não escolheu outra Skill."
    )
    print(
        "A explicação é determinística; relações e efetividade observadas "
        "não são tratadas como causalidade."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'ADAPTIVE COACH STRATEGY' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
