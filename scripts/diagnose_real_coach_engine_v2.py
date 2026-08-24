from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

load_dotenv(
    PROJECT_ROOT / ".env"
)


from src.coach.engine.coach_engine import CoachEngine


def _safe_text(
    value,
    default: str = "-",
) -> str:
    if value is None:
        return default

    text = str(value).strip()

    return text or default


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - REAL COACH ENGINE V2 DIAGNOSTIC")
    print("=" * 82)

    print()
    print(
        "Este diagnóstico chama diretamente o CoachEngine V2:"
    )
    print(
        "Player Analysis -> Skill Mapping -> Inspector -> coach_context -> "
        "Habits -> SkillSignals -> Evidence Fusion -> Learning Priority -> "
        "Training Plan -> TrainingMission -> CoachReport"
    )

    riot_id = input(
        "Riot ID (Game Name): "
    ).strip()

    tag = input(
        "Tag: "
    ).strip()

    benchmark_id = input(
        "Benchmark ID [advanced]: "
    ).strip() or "advanced"

    matches_raw = input(
        "Quantidade de partidas [30]: "
    ).strip() or "30"

    mission_games_raw = input(
        "Partidas no ciclo de treino [5]: "
    ).strip() or "5"

    use_cache_raw = input(
        "Usar cache? [S]: "
    ).strip().lower() or "s"

    try:
        match_count = int(
            matches_raw
        )
    except ValueError:
        match_count = 30

    try:
        mission_games_target = int(
            mission_games_raw
        )
    except ValueError:
        mission_games_target = 5

    use_cache = (
        use_cache_raw
        not in {
            "n",
            "nao",
            "não",
            "no",
            "false",
            "0",
        }
    )

    print()
    print("[1] Executando CoachEngine V2...")

    try:
        report = CoachEngine().analyze(
            game_name=riot_id,
            tag_line=tag,
            benchmark_id=benchmark_id,
            match_count=match_count,
            use_cache=use_cache,
            mission_games_target=(
                mission_games_target
            ),
        )
    except Exception as exc:
        print()
        print(
            "[ERRO] Falha ao executar CoachEngine V2:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print()
        print(
            "Envie o traceback completo para diagnóstico."
        )
        raise

    print("[OK] CoachReport recebido")

    print()
    print("=" * 82)
    print("COACH ENGINE V2 - RESULTADO REAL")
    print("=" * 82)

    analysis = report.analysis
    recommendation = (
        report.learning_recommendation
    )
    mission = report.mission

    print()
    print("ANÁLISE")
    print(
        "Jogador          : "
        f"{analysis.game_name}#{analysis.tag_line}"
    )
    print(
        "Benchmark        : "
        f"{analysis.benchmark_id}"
    )
    print(
        "Partidas         : "
        f"{len(analysis.match_ids)}"
    )
    print(
        "Elo atual        : "
        f"{_safe_text(analysis.current_rank)}"
    )
    print(
        "Estágio atual    : "
        f"{_safe_text(analysis.current_stage)}"
    )
    print(
        "Estágio-alvo     : "
        f"{_safe_text(analysis.target_stage)}"
    )

    print()
    print("COMPATIBILIDADE LEGADA")
    print(
        "LearningRecommendation ainda existe no CoachReport."
    )

    legacy_skill = getattr(
        recommendation,
        "skill",
        None,
    )

    print(
        "Skill legada     : "
        f"{_safe_text(getattr(legacy_skill, 'title', None))}"
    )
    print(
        "Skill ID legada  : "
        f"{_safe_text(getattr(legacy_skill, 'id', None))}"
    )

    print()
    print("MISSÃO REAL")
    print(
        "Skill da missão  : "
        f"{_safe_text(mission.skill_id)}"
    )
    print(
        "Título           : "
        f"{_safe_text(mission.title)}"
    )
    print(
        "Task ID          : "
        f"{_safe_text(mission.task.id)}"
    )
    print(
        "Objetivo/Hábito  : "
        f"{_safe_text(mission.task.habit)}"
    )
    print(
        "Ciclo            : "
        f"{mission.games_completed}/{mission.games_target}"
    )
    print(
        "Restantes        : "
        f"{mission.remaining_games}"
    )
    print(
        "Progresso        : "
        f"{mission.progress_percentage:.2f}%"
    )
    print(
        "Concluída        : "
        f"{'Sim' if mission.is_completed else 'Não'}"
    )

    print()
    print("CHECKLIST DA MISSÃO")

    checklist = tuple(
        mission.task.checklist
    )

    if checklist:
        for item in checklist:
            print(
                f"- {item}"
            )
    else:
        print("-")

    print()
    print("COACH MESSAGE")
    print(
        report.coach_message
    )

    print()
    print("=" * 82)
    print("VALIDAÇÕES IMPORTANTES")
    print("=" * 82)

    expected_task_by_skill = {
        "leveling": (
            "balance_level_and_stability"
        ),
        "consistency": (
            "define_simple_game_plan"
        ),
    }

    expected_task = (
        expected_task_by_skill.get(
            mission.skill_id
        )
    )

    if expected_task is None:
        task_status = (
            "N/A - Skill sem mapeamento específico "
            "neste diagnóstico."
        )
    else:
        task_status = (
            "OK"
            if mission.task.id
            == expected_task
            else (
                "ATENÇÃO - esperado "
                f"{expected_task}"
            )
        )

    print(
        "Task coerente com a Skill : "
        f"{task_status}"
    )

    legacy_skill_id = getattr(
        legacy_skill,
        "id",
        None,
    )

    if legacy_skill_id != mission.skill_id:
        print(
            "Legacy x nova missão     : "
            "DIFERENTES (permitido nesta fase de migração)"
        )
        print(
            "                         "
            "A missão nova é a decisão pedagógica ativa."
        )
    else:
        print(
            "Legacy x nova missão     : "
            "IGUAIS"
        )

    print()
    print("=" * 82)
    print("RESUMO")
    print("=" * 82)
    print(
        "LearningRecommendation legado : "
        f"{_safe_text(getattr(legacy_skill, 'title', None))}"
    )
    print(
        "Skill da missão nova          : "
        f"{_safe_text(mission.skill_id)}"
    )
    print(
        "Exercício real                : "
        f"{_safe_text(mission.title)}"
    )
    print(
        "Task ID                       : "
        f"{_safe_text(mission.task.id)}"
    )
    print(
        "Progresso                     : "
        f"{mission.games_completed}/"
        f"{mission.games_target}"
    )

    print()
    print(
        "Se a Skill legada e a Skill da missão forem diferentes, "
        "isso não significa bug nesta etapa. O fluxo novo decide a missão; "
        "o LearningRecommendation antigo permanece no relatório somente "
        "por compatibilidade."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'COACH ENGINE V2 - RESULTADO REAL' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
