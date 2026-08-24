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

from src.riot_client import RiotClient
from src.storage import PlayerRepository
from src.training.services.skill_training_history_aggregator import (
    SkillTrainingHistoryAggregator,
)


def main() -> None:
    print("=" * 82)
    print(
        "TFT INSIGHT - SKILL TRAINING HISTORY + TREND V1 - REAL"
    )
    print("=" * 82)

    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    riot_client = RiotClient()

    account = riot_client.get_account(
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

    repository = PlayerRepository()

    cycles = repository.list_training_cycles(
        puuid=puuid
    )

    summaries = (
        SkillTrainingHistoryAggregator.aggregate_all(
            training_history=cycles
        )
    )

    print()
    print("=" * 82)
    print("HISTÓRICO AGREGADO POR SKILL")
    print("=" * 82)
    print(
        f"Ciclos arquivados totais: {len(cycles)}"
    )

    if not summaries:
        print(
            "Nenhuma Skill possui ciclo arquivado."
        )

    for skill_id, summary in summaries.items():
        print()
        print("-" * 82)
        print(
            f"SKILL: {skill_id}"
        )
        print("-" * 82)
        print(
            f"Ciclos totais       : {summary.cycles_total}"
        )
        print(
            f"Ciclos avaliados    : {summary.evaluated_cycles}"
        )
        print(
            f"Ciclos conclusivos  : {summary.conclusive_cycles}"
        )
        print(
            f"POSITIVE            : {summary.positive_cycles}"
        )
        print(
            f"STABLE              : {summary.stable_cycles}"
        )
        print(
            f"NEGATIVE            : {summary.negative_cycles}"
        )
        print(
            f"INCONCLUSIVE        : {summary.inconclusive_cycles}"
        )
        print(
            f"Tendência            : {summary.trend}"
        )
        print(
            f"Confiança tendência  : {summary.trend_confidence}"
        )
        print(
            f"Último resultado     : {summary.latest_result or '-'}"
        )
        print(
            f"Resultado anterior   : {summary.previous_result or '-'}"
        )

        print()
        print("CICLOS")

        for index, cycle in enumerate(
            summary.cycles,
            start=1,
        ):
            print(
                f"{index}. "
                f"{cycle.task_title or cycle.task_id or '-'} "
                f"| {cycle.result or 'SEM AVALIAÇÃO'} "
                f"| {cycle.confidence or '-'}"
            )

        print()
        print("LEITURA")
        print(
            summary.rationale
        )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print(
        "A tendência usa apenas ciclos conclusivos da mesma Skill. "
        "INCONCLUSIVE não é transformado artificialmente em melhora ou piora."
    )
    print(
        "Nesta V1, a tendência descreve a sequência dos resultados de treino. "
        "Ela ainda não controla a próxima prioridade nem a dificuldade da task."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie desde 'HISTÓRICO AGREGADO POR SKILL' até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
