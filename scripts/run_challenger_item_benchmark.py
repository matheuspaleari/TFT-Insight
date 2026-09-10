"""
Aprende a classificação dos itens usando partidas de jogadores Challenger.

O script:

1. busca os melhores jogadores Challenger;
2. coleta os IDs das partidas recentes;
3. remove partidas duplicadas;
4. mantém cache local para permitir retomada;
5. processa todos os oito participantes de cada partida;
6. atualiza uma base estatística exclusiva do Challenger;
7. salva um relatório CSV com a classificação final.

Por padrão:
- 100 jogadores;
- 30 partidas por jogador;
- processamento em lotes de 25 partidas.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time
from typing import Any

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


from src.role_inference import (
    CommunityDragonClient,
    CommunityDragonItemParser,
    RichItemRepository,
)
from src.role_inference.repositories import (
    ItemObservationRepository,
)
from src.role_inference.services import (
    ItemCatalogClassifier,
    ItemLearningCycle,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


DEFAULT_PLAYERS = 100
DEFAULT_MATCHES_PER_PLAYER = 30
DEFAULT_BATCH_SIZE = 25
TARGET_SET_NUMBER = 18
TARGET_SET_CORE_NAME = "TFTSet18"
MATCH_SCAN_MULTIPLIER = 2.0

STATE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "challenger"
)

MATCH_CACHE_DIRECTORY = (
    STATE_DIRECTORY
    / "matches"
)

MATCH_INDEX_PATH = (
    STATE_DIRECTORY
    / "match_index.json"
)

OBSERVATIONS_PATH = (
    STATE_DIRECTORY
    / "item_observations.json"
)

REPORT_CSV_PATH = (
    STATE_DIRECTORY
    / "item_classifications.csv"
)

SUMMARY_JSON_PATH = (
    STATE_DIRECTORY
    / "summary.json"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classifica itens usando partidas "
            "do benchmark Challenger."
        )
    )

    parser.add_argument(
        "--players",
        type=int,
        default=DEFAULT_PLAYERS,
        help=(
            "Quantidade de jogadores Challenger. "
            f"Padrão: {DEFAULT_PLAYERS}."
        ),
    )

    parser.add_argument(
        "--matches-per-player",
        type=int,
        default=DEFAULT_MATCHES_PER_PLAYER,
        help=(
            "Partidas recentes solicitadas por jogador. "
            f"Padrão: {DEFAULT_MATCHES_PER_PLAYER}."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=(
            "Partidas processadas por ciclo de persistência. "
            f"Padrão: {DEFAULT_BATCH_SIZE}."
        ),
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Apaga observações, índice e cache Challenger "
            "antes de iniciar."
        ),
    )

    parser.add_argument(
        "--reset-learning",
        action="store_true",
        help=(
            "Apaga somente observações/relatórios e reinicia o estado "
            "de processamento, preservando IDs e cache das partidas."
        ),
    )

    parser.add_argument(
        "--refresh-communitydragon",
        action="store_true",
        help=(
            "Baixa novamente os dados completos "
            "do CommunityDragon."
        ),
    )

    return parser.parse_args()


def validate_arguments(
    args: argparse.Namespace,
) -> None:
    if args.players < 1:
        raise ValueError(
            "--players deve ser maior que zero."
        )

    if args.matches_per_player < 1:
        raise ValueError(
            "--matches-per-player deve ser maior que zero."
        )

    if args.batch_size < 1:
        raise ValueError(
            "--batch-size deve ser maior que zero."
        )

    if args.reset and args.reset_learning:
        raise ValueError(
            "Use apenas um modo de reset: --reset ou --reset-learning."
        )


def match_scan_limit(matches_per_player: int) -> int:
    return max(
        matches_per_player,
        round(matches_per_player * MATCH_SCAN_MULTIPLIER),
    )


def is_target_set_match(match_data: dict[str, Any]) -> bool:
    info = match_data.get("info")

    if not isinstance(info, dict):
        return False

    raw_set_number = info.get("tft_set_number")
    raw_core_name = info.get("tft_set_core_name")

    set_number: int | None = None

    try:
        if raw_set_number is not None:
            set_number = int(raw_set_number)
    except (TypeError, ValueError):
        set_number = None

    core_name = str(raw_core_name or "").strip()

    if set_number is not None:
        return set_number == TARGET_SET_NUMBER

    if core_name:
        return core_name.casefold() == TARGET_SET_CORE_NAME.casefold()

    return False


def reset_state() -> None:
    if not STATE_DIRECTORY.exists():
        return

    for path in sorted(
        STATE_DIRECTORY.rglob("*"),
        reverse=True,
    ):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()


def reset_learning_state() -> None:
    """
    Reinicia somente o aprendizado Challenger.

    Preserva:
    - match_index.json -> match_ids;
    - data/role_inference/challenger/matches/*.json.

    Remove:
    - observações aprendidas;
    - CSV e resumo;
    - marcações processed/failed, para reprocessar o cache existente.
    """
    for path in (
        OBSERVATIONS_PATH,
        REPORT_CSV_PATH,
        SUMMARY_JSON_PATH,
    ):
        if path.exists():
            path.unlink()

    index = load_index()

    # Os IDs coletados são mantidos. Apenas o estado derivado do
    # processamento/aprendizado é reiniciado.
    index["processed_match_ids"] = []
    index["failed_match_ids"] = {}
    index["discarded_other_set"] = 0
    index["accepted_set_matches"] = 0
    index["target_set_number"] = TARGET_SET_NUMBER
    index["target_set_core_name"] = TARGET_SET_CORE_NAME

    save_index(index)

    cached_matches = (
        sum(
            1
            for path in MATCH_CACHE_DIRECTORY.glob("*.json")
            if path.is_file()
        )
        if MATCH_CACHE_DIRECTORY.exists()
        else 0
    )

    print(
        "Aprendizado reiniciado seletivamente · "
        f"{cached_matches} partidas em cache preservadas · "
        f"{len(index.get('match_ids', {}))} IDs preservados."
    )


def load_rich_items() -> dict:
    repository = RichItemRepository()

    if (
        repository.exists()
        and not ARGS.refresh_communitydragon
    ):
        print(
            "Carregando CommunityDragon do cache..."
        )
        payload = repository.load()

    else:
        print(
            "Baixando CommunityDragon..."
        )
        payload = (
            CommunityDragonClient()
            .get_tft_data()
        )
        repository.save(payload)

    items = (
        CommunityDragonItemParser.parse(
            payload
        )
    )

    if not items:
        raise RuntimeError(
            "Nenhum item foi extraído do CommunityDragon."
        )

    print(
        f"Itens completos carregados: "
        f"{len(items)}"
    )

    return items


def load_index() -> dict[str, Any]:
    if not MATCH_INDEX_PATH.exists():
        return {
            "match_ids": {},
            "processed_match_ids": [],
            "failed_match_ids": {},
        }

    data = json.loads(
        MATCH_INDEX_PATH.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(data, dict):
        raise RuntimeError(
            "O índice Challenger possui formato inválido."
        )

    return data


def save_index(
    index: dict[str, Any],
) -> None:
    MATCH_INDEX_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    MATCH_INDEX_PATH.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def collect_match_ids(
    *,
    riot_client: RiotClient,
    players_limit: int,
    matches_per_player: int,
    index: dict[str, Any],
) -> dict[str, str]:
    """
    Retorna match_id -> PUUID usado para transformar a partida.
    """

    existing = index.get(
        "match_ids",
        {},
    )

    if isinstance(existing, dict) and existing:
        print(
            "Usando índice de partidas já coletado: "
            f"{len(existing)} partidas únicas."
        )

        return {
            str(match_id): str(puuid)
            for match_id, puuid
            in existing.items()
        }

    print(
        f"Buscando {players_limit} jogadores Challenger..."
    )

    entries = riot_client.get_apex_league_players(
        tier="CHALLENGER",
        limit=players_limit,
        queue="RANKED_TFT",
    )

    if not entries:
        raise RuntimeError(
            "Nenhum jogador Challenger foi encontrado."
        )

    match_to_puuid: dict[str, str] = {}

    for index_number, entry in enumerate(
        entries,
        start=1,
    ):
        puuid = str(
            entry.get("puuid", "")
            or entry.get("summonerId", "")
        ).strip()

        if not puuid:
            print(
                f"[{index_number}/{len(entries)}] "
                "Jogador ignorado: sem PUUID."
            )
            continue

        try:
            match_ids = riot_client.get_match_ids(
                puuid=puuid,
                count=match_scan_limit(matches_per_player),
            )

        except RuntimeError as error:
            print(
                f"[{index_number}/{len(entries)}] "
                f"Falha ao buscar partidas: {error}"
            )
            continue

        before = len(match_to_puuid)

        for match_id in match_ids:
            match_to_puuid.setdefault(
                match_id,
                puuid,
            )

        added = (
            len(match_to_puuid)
            - before
        )

        print(
            f"[{index_number}/{len(entries)}] "
            f"{len(match_ids)} IDs recebidos (scan) · "
            f"{added} novos · "
            f"{len(match_to_puuid)} únicos"
        )

    if not match_to_puuid:
        raise RuntimeError(
            "Nenhum ID de partida Challenger foi coletado."
        )

    index["match_ids"] = match_to_puuid
    save_index(index)

    return match_to_puuid


def cache_path_for(
    match_id: str,
) -> Path:
    return (
        MATCH_CACHE_DIRECTORY
        / f"{match_id}.json"
    )


def load_or_download_match(
    *,
    riot_client: RiotClient,
    match_id: str,
) -> dict[str, Any]:
    path = cache_path_for(match_id)

    if path.exists():
        data = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

        if isinstance(data, dict):
            return data

    data = riot_client.get_match_details(
        match_id=match_id,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return data


def process_matches(
    *,
    riot_client: RiotClient,
    rich_items: dict,
    match_to_puuid: dict[str, str],
    index: dict[str, Any],
    batch_size: int,
) -> None:
    processed = set(
        str(match_id)
        for match_id in index.get(
            "processed_match_ids",
            [],
        )
    )

    failed = dict(
        index.get(
            "failed_match_ids",
            {},
        )
        or {}
    )

    pending = [
        (
            match_id,
            puuid,
        )
        for match_id, puuid
        in match_to_puuid.items()
        if (
            match_id not in processed
            and match_id not in failed
        )
    ]

    print()
    print(
        f"Partidas únicas       : "
        f"{len(match_to_puuid)}"
    )
    print(
        f"Já processadas        : "
        f"{len(processed)}"
    )
    print(
        f"Pendentes             : "
        f"{len(pending)}"
    )
    print(
        f"Falhas anteriores     : "
        f"{len(failed)}"
    )

    if not pending:
        print(
            "Nenhuma partida pendente."
        )
        return

    observation_repository = (
        ItemObservationRepository(
            path=OBSERVATIONS_PATH
        )
    )

    learning_cycle = ItemLearningCycle(
        observation_repository=(
            observation_repository
        )
    )

    batch = []
    started_at = time.monotonic()
    discarded_other_set = 0
    accepted_set_matches = 0

    for position, (
        match_id,
        puuid,
    ) in enumerate(
        pending,
        start=1,
    ):
        try:
            match_data = load_or_download_match(
                riot_client=riot_client,
                match_id=match_id,
            )

            if not is_target_set_match(match_data):
                discarded_other_set += 1
                processed.add(match_id)

                index["processed_match_ids"] = sorted(processed)
                index["failed_match_ids"] = failed
                index["target_set_number"] = TARGET_SET_NUMBER
                index["target_set_core_name"] = TARGET_SET_CORE_NAME
                index["discarded_other_set"] = discarded_other_set
                save_index(index)
                continue

            match = MatchTransformer.transform(
                match_data=match_data,
                puuid=puuid,
            )

            batch.append(match)
            accepted_set_matches += 1

        except (
            RuntimeError,
            ValueError,
            KeyError,
            json.JSONDecodeError,
        ) as error:
            failed[match_id] = str(error)

            print(
                f"[{position}/{len(pending)}] "
                f"{match_id} falhou: {error}"
            )

        should_flush = (
            len(batch) >= batch_size
            or position == len(pending)
        )

        if should_flush and batch:
            learning_cycle.run(
                matches=batch,
                items=rich_items,
            )

            for match in batch:
                processed.add(
                    match.match_id
                )

            index[
                "processed_match_ids"
            ] = sorted(processed)

            index[
                "failed_match_ids"
            ] = failed
            index["target_set_number"] = TARGET_SET_NUMBER
            index["target_set_core_name"] = TARGET_SET_CORE_NAME
            index["discarded_other_set"] = discarded_other_set
            index["accepted_set_matches"] = accepted_set_matches

            save_index(index)

            elapsed = (
                time.monotonic()
                - started_at
            )

            print(
                f"[{position}/{len(pending)}] "
                f"Lote salvo · "
                f"{len(processed)}/"
                f"{len(match_to_puuid)} processadas · "
                f"{elapsed:.1f}s"
            )

            batch.clear()

    index["processed_match_ids"] = sorted(
        processed
    )
    index["failed_match_ids"] = failed
    index["target_set_number"] = TARGET_SET_NUMBER
    index["target_set_core_name"] = TARGET_SET_CORE_NAME
    index["discarded_other_set"] = discarded_other_set
    index["accepted_set_matches"] = accepted_set_matches
    save_index(index)


def save_report(
    *,
    rich_items: dict,
) -> None:
    observation_repository = (
        ItemObservationRepository(
            path=OBSERVATIONS_PATH
        )
    )

    observations = (
        observation_repository.load_all()
    )

    classifications = (
        ItemCatalogClassifier.classify_all(
            items=rich_items,
            observations=observations,
        )
    )

    rows = []

    for item_id, observation in observations.items():
        classification = classifications.get(
            item_id
        )

        if classification is None:
            continue

        item = rich_items.get(item_id)

        rows.append(
            {
                "item_id": item_id,
                "item_name": (
                    item.name
                    if item is not None
                    else item_id
                ),
                "category": (
                    classification.category.value
                ),
                "confidence": (
                    classification.confidence
                ),
                "offense_score": (
                    classification.offense_score
                ),
                "defense_score": (
                    classification.defense_score
                ),
                "utility_score": (
                    classification.utility_score
                ),
                "total_uses": (
                    observation.total_uses
                ),
                "carry_uses": (
                    observation.damage_carry_uses
                ),
                "tank_uses": (
                    observation.tank_uses
                ),
                "support_uses": (
                    observation.support_uses
                ),
                "source": classification.source,
            }
        )

    rows.sort(
        key=lambda row: (
            row["total_uses"],
            row["confidence"],
        ),
        reverse=True,
    )

    REPORT_CSV_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "item_id",
                "item_name",
                "category",
                "confidence",
                "offense_score",
                "defense_score",
                "utility_score",
                "total_uses",
                "carry_uses",
                "tank_uses",
                "support_uses",
                "source",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    index = load_index()

    summary = {
        "players_requested": ARGS.players,
        "matches_per_player": (
            ARGS.matches_per_player
        ),
        "match_scan_limit": match_scan_limit(
            ARGS.matches_per_player
        ),
        "target_set_number": TARGET_SET_NUMBER,
        "target_set_core_name": TARGET_SET_CORE_NAME,
        "unique_matches": len(
            index.get("match_ids", {})
        ),
        "processed_matches": len(
            index.get(
                "processed_match_ids",
                [],
            )
        ),
        "failed_matches": len(
            index.get(
                "failed_match_ids",
                {},
            )
        ),
        "discarded_other_set": int(
            index.get("discarded_other_set", 0) or 0
        ),
        "accepted_set_matches": int(
            index.get("accepted_set_matches", 0) or 0
        ),
        "classified_items": len(rows),
        "observations_path": str(
            OBSERVATIONS_PATH
        ),
        "report_csv_path": str(
            REPORT_CSV_PATH
        ),
    }

    SUMMARY_JSON_PATH.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 110)
    print(
        "TFT INSIGHT - ITENS DO BENCHMARK CHALLENGER"
    )
    print("=" * 110)

    print(
        f"Partidas únicas       : "
        f"{summary['unique_matches']}"
    )
    print(
        f"Partidas processadas  : "
        f"{summary['processed_matches']}"
    )
    print(
        f"Partidas com falha    : "
        f"{summary['failed_matches']}"
    )
    print(
        f"Set alvo              : "
        f"{summary['target_set_core_name']}"
    )
    print(
        f"Partidas Set alvo     : "
        f"{summary['accepted_set_matches']}"
    )
    print(
        f"Outros Sets descart.  : "
        f"{summary['discarded_other_set']}"
    )
    print(
        f"Itens observados      : "
        f"{summary['classified_items']}"
    )

    print()
    print(
        f"{'ITEM':<40} "
        f"{'CATEGORIA':<13} "
        f"{'CONF.':>7} "
        f"{'USOS':>7} "
        f"{'CARRY':>7} "
        f"{'TANK':>7} "
        f"{'SUP':>7}"
    )
    print("-" * 110)

    for row in rows[:30]:
        print(
            f"{row['item_name'][:39]:<40} "
            f"{row['category']:<13} "
            f"{row['confidence']:>6.1f}% "
            f"{row['total_uses']:>7} "
            f"{row['carry_uses']:>7} "
            f"{row['tank_uses']:>7} "
            f"{row['support_uses']:>7}"
        )

    print()
    print(
        f"Observações: {OBSERVATIONS_PATH}"
    )
    print(
        f"Relatório CSV: {REPORT_CSV_PATH}"
    )
    print(
        f"Resumo: {SUMMARY_JSON_PATH}"
    )
    print()
    print(
        "✓ Benchmark Challenger de itens concluído."
    )


def main() -> None:
    validate_arguments(ARGS)

    if ARGS.reset:
        print(
            "Limpando dados anteriores "
            "do benchmark Challenger..."
        )
        reset_state()

    elif ARGS.reset_learning:
        print(
            "Reiniciando somente o aprendizado Challenger "
            "(cache de partidas será preservado)..."
        )
        reset_learning_state()

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    rich_items = load_rich_items()
    riot_client = RiotClient()
    index = load_index()

    print(
        f"Set alvo            : {TARGET_SET_CORE_NAME} "
        f"({TARGET_SET_NUMBER})"
    )
    print(
        f"Scan por jogador    : "
        f"{match_scan_limit(ARGS.matches_per_player)} IDs recentes"
    )

    match_to_puuid = collect_match_ids(
        riot_client=riot_client,
        players_limit=ARGS.players,
        matches_per_player=(
            ARGS.matches_per_player
        ),
        index=index,
    )

    process_matches(
        riot_client=riot_client,
        rich_items=rich_items,
        match_to_puuid=match_to_puuid,
        index=index,
        batch_size=ARGS.batch_size,
    )

    save_report(
        rich_items=rich_items
    )


ARGS = parse_arguments()


if __name__ == "__main__":
    main()
