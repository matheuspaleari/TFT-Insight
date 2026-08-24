from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.coach_intelligence import AdaptiveIntelligenceFoundation
from src.learning import SkillMappingService
from src.riot_client import RiotClient
from src.services import PlayerAnalysisService
from src.storage import PlayerRepository


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - FASE 11.1 A 11.4 - DIAGNÓSTICO REAL")
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
    puuid = str(account.get("puuid", ""))

    if not puuid:
        raise RuntimeError("PUUID não retornado pela Riot.")

    analysis = PlayerAnalysisService().analyze(
        game_name=game_name,
        tag_line=tag_line,
        benchmark_id=benchmark_id,
        match_count=30,
        use_cache=True,
    )

    assessments = SkillMappingService.assess(
        performance=analysis.performance
    )

    repo = PlayerRepository()
    memory = repo.load_pedagogical_memory(
        puuid=puuid
    )
    history = repo.list_training_cycles(
        puuid=puuid
    )

    result = AdaptiveIntelligenceFoundation.build(
        puuid=puuid,
        assessments=assessments,
        pedagogical_memory=memory,
        training_history=history,
        current_priority_skill_id=priority,
        player_repository=repo,
        persist=True,
    )

    print()
    print("=" * 82)
    print("PLAYER LEARNING PROFILE")
    print("=" * 82)

    skills = result["profile"]["skills"]
    for skill_id, item in skills.items():
        print()
        print(f"SKILL: {skill_id}")
        print(f"  Estado       : {item['state']}")
        print(f"  Score        : {item['score'] if item['score'] is not None else '-'}")
        print(f"  Nível        : {item['level']}")
        print(f"  Tendência    : {item['trend']}")
        print(f"  Ciclos       : {item['cycles_total']}")
        print(f"  Conclusivos  : {item['conclusive_cycles']}")
        print(f"  Dificuldade  : {item['current_difficulty'] or '-'}")

    print()
    print("=" * 82)
    print("SKILL EVOLUTION")
    print("=" * 82)
    for item in result["evolution"]:
        print(
            f"{item['skill_id']}: "
            f"{item['direction']} | "
            f"delta={item['score_delta'] if item['score_delta'] is not None else '-'} | "
            f"confiança={item['confidence']}"
        )

    print()
    print("=" * 82)
    print("CROSS-SKILL")
    print("=" * 82)
    if not result["cross_skill_insights"]:
        print("Nenhum sinal cross-skill relevante com evidência suficiente.")
    else:
        for item in result["cross_skill_insights"]:
            print(
                f"{item['relationship_id']}: "
                f"{item['status']} | {item['confidence']}"
            )
            print(f"  {item['rationale']}")
            print(f"  Limitação: {item['limitation']}")

    print()
    print("=" * 82)
    print("TRAINING EFFECTIVENESS")
    print("=" * 82)
    if not result["training_effectiveness"]:
        print("Ainda não há exercícios avaliados.")
    else:
        for item in result["training_effectiveness"]:
            print()
            print(
                f"{item['skill_id']} / {item['task_id']}"
            )
            print(
                f"  Efetividade : {item['effectiveness']}"
            )
            print(
                f"  Confiança   : {item['confidence']}"
            )
            print(
                "  Resultados   : "
                f"+{item['positive_cycles']} / "
                f"={item['stable_cycles']} / "
                f"-{item['negative_cycles']} / "
                f"?{item['inconclusive_cycles']}"
            )

    print()
    print("=" * 82)
    print("PERSISTÊNCIA")
    print("=" * 82)
    print(
        "Arquivo: "
        + str(
            repo.get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "learning_profile.json"
        )
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "As fases 11.1-11.4 são somente inteligência observacional. "
        "Elas ainda NÃO alteram Learning Priority, missão ou Learning Loop."
    )
    print(
        "Cross-Skill e Training Effectiveness descrevem associações "
        "observadas e não atribuem causalidade."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'PLAYER LEARNING PROFILE' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
