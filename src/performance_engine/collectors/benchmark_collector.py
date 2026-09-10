"""
Coleta e construção de benchmarks por grupo competitivo.

Inclui:
- filtro explícito por Set;
- cache imediato de cada payload de partida baixado;
- checkpoint por jogador aceito para retomada após interrupção.
"""

from __future__ import annotations

import json
from pathlib import Path
import pickle
import time
from typing import Any

from src.benchmark import (
    BenchmarkPlayerCatalogEntry,
    LeaguePlayer,
    LeaguePlayerProvider,
    get_benchmark_group_configuration,
    metrics_to_dict,
    utc_now_iso,
)
from src.performance_engine.calculators import (
    BenchmarkCalculator,
    PlayerMetricsCalculator,
)
from src.performance_engine.models import (
    Benchmark,
    PlayerMetrics,
)
from src.riot_client import RiotClient
from src.transformers.match_transformer import (
    MatchTransformer,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

BENCHMARK_MATCH_CACHE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "match_cache"
)

BENCHMARK_CHECKPOINT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "checkpoints"
)

CHECKPOINT_VERSION = 2
DEFAULT_MINIMUM_VALID_MATCHES = 5


class BenchmarkCollector:
    """
    Coleta partidas de jogadores pertencentes a um grupo competitivo.

    O Collector:

    - obtém candidatos pelo LeaguePlayerProvider;
    - busca IDs de partidas recentes;
    - mantém cache local dos payloads Riot por match_id;
    - reutiliza partidas já baixadas após interrupções;
    - aceita apenas partidas do Set configurado;
    - por padrão aceita jogador com pelo menos 5 partidas válidas;
    - usa no máximo matches_per_player partidas por jogador;
    - salva checkpoint após CADA jogador aceito;
    - retoma automaticamente jogadores já concluídos;
    - se o provider oferecer menos jogadores que a meta configurada,
      finaliza com todos os jogadores válidos realmente disponíveis;
    - consolida as métricas em um Benchmark.

    O checkpoint é local e interno ao TFT Insight. Ele usa pickle apenas
    para preservar exatamente os objetos PlayerMetrics e catálogo entre
    execuções do mesmo código.
    """

    def __init__(
        self,
        riot_client: RiotClient,
        match_transformer: MatchTransformer,
        metrics_calculator: PlayerMetricsCalculator,
        benchmark_calculator: BenchmarkCalculator,
        player_provider: LeaguePlayerProvider | None = None,
    ) -> None:
        self.riot_client = riot_client
        self.match_transformer = match_transformer
        self.metrics_calculator = metrics_calculator
        self.benchmark_calculator = benchmark_calculator
        self.player_provider = (
            player_provider
            or LeaguePlayerProvider(
                riot_client=riot_client,
            )
        )

        self.last_player_catalog: list[
            BenchmarkPlayerCatalogEntry
        ] = []

    def collect(
        self,
        *,
        benchmark_id: str,
        queue: str = "RANKED_TFT",
        minimum_valid_matches: int | None = None,
    ) -> Benchmark:
        started_at = time.monotonic()

        configuration = (
            get_benchmark_group_configuration(
                benchmark_id
            )
        )

        matches_per_player = (
            configuration.matches_per_player
        )

        match_scan_limit = (
            configuration.match_scan_limit
        )

        required_valid_matches = (
            DEFAULT_MINIMUM_VALID_MATCHES
            if minimum_valid_matches is None
            else minimum_valid_matches
        )

        self._validate_collection_parameters(
            target_valid_players=(
                configuration.target_valid_players
            ),
            matches_per_player=matches_per_player,
            match_scan_limit=match_scan_limit,
            minimum_valid_matches=(
                required_valid_matches
            ),
            target_set_number=(
                configuration.target_set_number
            ),
            target_set_core_name=(
                configuration.target_set_core_name
            ),
            queue=queue,
        )

        print()
        print("=" * 80)
        print("TFT INSIGHT - COLETA DE BENCHMARK")
        print("=" * 80)
        print(
            f"Benchmark           : "
            f"{configuration.benchmark_id}"
        )
        print(
            f"Nome                : "
            f"{configuration.display_name}"
        )
        print(
            f"Meta de jogadores   : "
            f"{configuration.target_valid_players}"
        )
        print(
            f"Máximo por jogador  : "
            f"{matches_per_player}"
        )
        print(
            f"Mínimo por jogador  : "
            f"{required_valid_matches}"
        )
        print(
            f"IDs recentes/scan   : "
            f"{match_scan_limit}"
        )
        print(
            f"Set alvo            : "
            f"{configuration.target_set_core_name} "
            f"({configuration.target_set_number})"
        )
        print(
            f"Cache de partidas   : "
            f"{BENCHMARK_MATCH_CACHE_DIRECTORY}"
        )
        print(
            f"Checkpoint usuários : "
            f"{BENCHMARK_CHECKPOINT_DIRECTORY}"
        )
        print("-" * 80)

        collected_metrics = (
            self.collect_players_metrics(
                benchmark_id=benchmark_id,
                queue=queue,
                minimum_valid_matches=(
                    required_valid_matches
                ),
            )
        )

        total_matches = sum(
            metrics.general.matches_played
            for _, metrics in collected_metrics
        )

        benchmark = (
            self.benchmark_calculator.calculate(
                metrics=[
                    metrics
                    for _, metrics
                    in collected_metrics
                ],
                name=(
                    f"{configuration.display_name} BR"
                ),
                total_matches=total_matches,
            )
        )

        elapsed = time.monotonic() - started_at

        print()
        print("-" * 80)
        print(
            f"Jogadores analisados: "
            f"{benchmark.players_analyzed}"
        )
        print(
            f"Partidas analisadas : "
            f"{benchmark.matches_analyzed}"
        )
        print(
            f"Tempo total         : "
            f"{elapsed:.2f}s"
        )
        print("=" * 80)

        return benchmark

    def collect_players_metrics(
        self,
        *,
        benchmark_id: str,
        queue: str = "RANKED_TFT",
        minimum_valid_matches: int | None = None,
    ) -> list[tuple[str, PlayerMetrics]]:
        """
        Coleta métricas até atingir a meta de jogadores válidos.

        Retomada:
        - cada partida baixada é salva imediatamente no match_cache;
        - cada jogador ACEITO é salvo imediatamente em checkpoint;
        - ao reiniciar, os jogadores aceitos são restaurados;
        - o candidato que estava no meio é reprocessado usando cache.
        """

        configuration = (
            get_benchmark_group_configuration(
                benchmark_id
            )
        )

        matches_per_player = (
            configuration.matches_per_player
        )

        match_scan_limit = (
            configuration.match_scan_limit
        )

        required_valid_matches = (
            DEFAULT_MINIMUM_VALID_MATCHES
            if minimum_valid_matches is None
            else minimum_valid_matches
        )

        self._validate_collection_parameters(
            target_valid_players=(
                configuration.target_valid_players
            ),
            matches_per_player=matches_per_player,
            match_scan_limit=match_scan_limit,
            minimum_valid_matches=(
                required_valid_matches
            ),
            target_set_number=(
                configuration.target_set_number
            ),
            target_set_core_name=(
                configuration.target_set_core_name
            ),
            queue=queue,
        )

        checkpoint_signature = (
            self._checkpoint_signature(
                benchmark_id=benchmark_id,
                target_valid_players=(
                    configuration.target_valid_players
                ),
                matches_per_player=matches_per_player,
                minimum_valid_matches=(
                    required_valid_matches
                ),
                target_set_number=(
                    configuration.target_set_number
                ),
                target_set_core_name=(
                    configuration.target_set_core_name
                ),
                queue=queue,
            )
        )

        (
            collected_metrics,
            restored_catalog,
            accepted_puuids,
            checkpoint_complete,
        ) = self._load_player_checkpoint(
            expected_signature=checkpoint_signature,
        )

        self.last_player_catalog = (
            restored_catalog
        )

        restored_players_count = len(
            collected_metrics
        )

        if checkpoint_complete and collected_metrics:
            print()
            print(
                "Checkpoint concluído encontrado: "
                f"{restored_players_count} jogadores válidos."
            )
            return collected_metrics

        if collected_metrics:
            print()
            print(
                "Retomando checkpoint: "
                f"{len(collected_metrics)}/"
                f"{configuration.target_valid_players} "
                "jogadores já concluídos."
            )

        if (
            len(collected_metrics)
            >= configuration.target_valid_players
        ):
            print(
                "Checkpoint já contém a meta completa "
                "de jogadores."
            )
            return collected_metrics[
                : configuration.target_valid_players
            ]

        candidates = self.player_provider.get_players(
            benchmark_id=benchmark_id,
        )

        if not candidates:
            raise RuntimeError(
                "O Provider não retornou candidatos "
                f"para o benchmark '{benchmark_id}'."
            )

        print(
            f"Candidatos disponíveis: "
            f"{len(candidates)}"
        )

        pool_limited = (
            len(candidates)
            < configuration.target_valid_players
        )

        effective_target_players = min(
            configuration.target_valid_players,
            max(
                restored_players_count,
                len(candidates),
            ),
        )

        if pool_limited:
            print(
                "Meta efetiva inicial: "
                f"{effective_target_players} jogadores "
                "(pool menor que a meta configurada)."
            )

        if (
            len(collected_metrics)
            >= effective_target_players
        ):
            print(
                "Checkpoint já contém a meta efetiva "
                "de jogadores."
            )
            self._save_player_checkpoint(
                signature=checkpoint_signature,
                collected_metrics=collected_metrics,
                player_catalog=self.last_player_catalog,
                accepted_puuids=accepted_puuids,
                complete=True,
            )
            return collected_metrics[
                :effective_target_players
            ]

        attempted_players = 0
        skipped_checkpoint_players = 0
        discarded_players = 0
        cache_hits_total = 0
        downloads_total = 0

        for candidate in candidates:
            if (
                len(collected_metrics)
                >= effective_target_players
            ):
                break

            candidate_puuid = str(
                candidate.puuid
            ).strip()

            if (
                candidate_puuid
                and candidate_puuid
                in accepted_puuids
            ):
                skipped_checkpoint_players += 1
                continue

            attempted_players += 1

            current_valid = len(
                collected_metrics
            )

            print()
            print(
                f"[{attempted_players}/{len(candidates)}] "
                f"{candidate.rank_label} · "
                f"válidos {current_valid}/"
                f"{effective_target_players}"
            )

            (
                player_metrics,
                cache_hits,
                downloads,
            ) = self._collect_player_metrics(
                player=candidate,
                matches_per_player=(
                    matches_per_player
                ),
                match_scan_limit=(
                    match_scan_limit
                ),
                minimum_valid_matches=(
                    required_valid_matches
                ),
                target_set_number=(
                    configuration.target_set_number
                ),
                target_set_core_name=(
                    configuration.target_set_core_name
                ),
            )

            cache_hits_total += cache_hits
            downloads_total += downloads

            if player_metrics is None:
                discarded_players += 1
                print(
                    "  Descartado: amostra de partidas "
                    "válidas do Set alvo insuficiente."
                )
                continue

            player_identifier = (
                self._resolve_player_identifier(
                    player=candidate,
                )
            )

            collected_metrics.append(
                (
                    player_identifier,
                    player_metrics,
                )
            )

            catalog_entry = (
                self._build_catalog_entry(
                    benchmark_id=benchmark_id,
                    player=candidate,
                    player_metrics=player_metrics,
                    queue=queue,
                )
            )

            self.last_player_catalog.append(
                catalog_entry
            )

            if candidate_puuid:
                accepted_puuids.add(
                    candidate_puuid
                )

            # CHECKPOINT IMEDIATO APÓS CADA USUÁRIO ACEITO.
            self._save_player_checkpoint(
                signature=checkpoint_signature,
                collected_metrics=(
                    collected_metrics
                ),
                player_catalog=(
                    self.last_player_catalog
                ),
                accepted_puuids=(
                    accepted_puuids
                ),
                complete=(
                    len(collected_metrics)
                    >= effective_target_players
                ),
            )

            print(
                "  Aceito + checkpoint salvo: "
                f"{player_identifier} · "
                f"{player_metrics.general.matches_played} "
                "partidas válidas."
            )

        valid_players = len(
            collected_metrics
        )

        print()
        print("-" * 80)
        print(
            f"Jogadores restaurados: "
            f"{restored_players_count}"
        )
        print(
            f"Candidatos já no checkpoint: "
            f"{skipped_checkpoint_players}"
        )
        print(
            f"Candidatos tentados nesta execução: "
            f"{attempted_players}"
        )
        print(
            f"Meta configurada    : "
            f"{configuration.target_valid_players}"
        )
        print(
            f"Meta efetiva inicial: "
            f"{effective_target_players}"
        )
        print(
            f"Jogadores válidos totais: "
            f"{valid_players}"
        )
        print(
            f"Jogadores descartados nesta execução: "
            f"{discarded_players}"
        )
        print(
            f"Cache reutilizado   : "
            f"{cache_hits_total} partidas"
        )
        print(
            f"Novos downloads     : "
            f"{downloads_total} partidas"
        )

        if (
            valid_players
            < effective_target_players
        ):
            if pool_limited and valid_players > 0:
                effective_target_players = valid_players
                print(
                    "Pool de candidatos esgotado antes da meta inicial. "
                    "Benchmark será finalizado com todos os jogadores "
                    f"válidos disponíveis: {effective_target_players}."
                )
            else:
                raise RuntimeError(
                    "Não foi possível atingir a meta efetiva do benchmark "
                    f"'{benchmark_id}'. "
                    f"Meta configurada: {configuration.target_valid_players}; "
                    f"meta efetiva: {effective_target_players}; "
                    f"válidos: {valid_players}; "
                    f"candidatos disponíveis: {len(candidates)}. "
                    "O checkpoint foi preservado; uma próxima "
                    "execução continuará a partir dos jogadores "
                    "já aceitos."
                )

        self._save_player_checkpoint(
            signature=checkpoint_signature,
            collected_metrics=(
                collected_metrics
            ),
            player_catalog=(
                self.last_player_catalog
            ),
            accepted_puuids=(
                accepted_puuids
            ),
            complete=True,
        )

        return collected_metrics

    def _collect_player_metrics(
        self,
        *,
        player: LeaguePlayer,
        matches_per_player: int,
        match_scan_limit: int,
        minimum_valid_matches: int,
        target_set_number: int,
        target_set_core_name: str,
    ) -> tuple[
        PlayerMetrics | None,
        int,
        int,
    ]:
        try:
            match_ids = (
                self.riot_client.get_match_ids(
                    puuid=player.puuid,
                    count=match_scan_limit,
                )
            )
        except (
            RuntimeError,
            ValueError,
            KeyError,
        ) as error:
            print(
                "  Falha ao buscar partidas: "
                f"{error}"
            )
            return None, 0, 0

        if (
            len(match_ids)
            < minimum_valid_matches
        ):
            print(
                "  Partidas encontradas: "
                f"{len(match_ids)}/"
                f"{minimum_valid_matches} exigidas."
            )
            return None, 0, 0

        matches = []
        discarded_other_set = 0
        invalid_matches = 0
        cache_hits = 0
        downloads = 0

        for match_index, match_id in enumerate(
            match_ids,
            start=1,
        ):
            if (
                len(matches)
                >= matches_per_player
            ):
                break

            try:
                (
                    match_data,
                    from_cache,
                ) = self._load_or_download_match(
                    match_id=match_id,
                )

                if from_cache:
                    cache_hits += 1
                else:
                    downloads += 1

                if not self._is_target_set_match(
                    match_data=match_data,
                    target_set_number=(
                        target_set_number
                    ),
                    target_set_core_name=(
                        target_set_core_name
                    ),
                ):
                    discarded_other_set += 1
                    continue

                match = (
                    self.match_transformer.transform(
                        match_data=match_data,
                        puuid=player.puuid,
                    )
                )

                matches.append(
                    match
                )

            except (
                RuntimeError,
                ValueError,
                KeyError,
                json.JSONDecodeError,
                OSError,
            ) as error:
                invalid_matches += 1
                print(
                    "  Partida inválida "
                    f"{match_index}/{len(match_ids)}: "
                    f"{error}"
                )

        print(
            f"  Set alvo aceitas   : "
            f"{len(matches)}"
        )
        print(
            f"  Outros Sets        : "
            f"{discarded_other_set}"
        )
        print(
            f"  Cache reutilizado  : "
            f"{cache_hits}"
        )
        print(
            f"  Novos downloads    : "
            f"{downloads}"
        )
        print(
            f"  Inválidas          : "
            f"{invalid_matches}"
        )

        if (
            len(matches)
            < minimum_valid_matches
        ):
            print(
                "  Partidas válidas do Set alvo: "
                f"{len(matches)}/"
                f"{minimum_valid_matches} exigidas."
            )
            return (
                None,
                cache_hits,
                downloads,
            )

        try:
            metrics = (
                self.metrics_calculator.calculate(
                    matches
                )
            )

            return (
                metrics,
                cache_hits,
                downloads,
            )

        except (
            RuntimeError,
            ValueError,
            KeyError,
        ) as error:
            print(
                "  Falha ao calcular métricas: "
                f"{error}"
            )
            return (
                None,
                cache_hits,
                downloads,
            )

    def _load_or_download_match(
        self,
        *,
        match_id: str,
    ) -> tuple[
        dict[str, Any],
        bool,
    ]:
        """
        Carrega uma partida do cache local ou baixa da Riot.

        Cada download bem-sucedido é persistido imediatamente.
        """

        cache_path = (
            self._cache_path_for(
                match_id=match_id,
            )
        )

        if cache_path.exists():
            try:
                payload = json.loads(
                    cache_path.read_text(
                        encoding="utf-8"
                    )
                )
            except (
                json.JSONDecodeError,
                OSError,
            ):
                payload = None

            if isinstance(
                payload,
                dict,
            ):
                return (
                    payload,
                    True,
                )

            try:
                cache_path.unlink()
            except OSError:
                pass

        payload = (
            self.riot_client
            .get_match_details(
                match_id=match_id,
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise RuntimeError(
                "Riot API retornou payload de "
                "partida inválido para "
                f"{match_id}."
            )

        cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            cache_path.with_suffix(
                ".json.tmp"
            )
        )

        temporary_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            cache_path
        )

        return (
            payload,
            False,
        )

    @staticmethod
    def _cache_path_for(
        *,
        match_id: str,
    ) -> Path:
        safe_match_id = (
            str(match_id)
            .strip()
            .replace("/", "_")
            .replace("\\", "_")
        )

        if not safe_match_id:
            raise ValueError(
                "match_id vazio não pode ser "
                "armazenado em cache."
            )

        return (
            BENCHMARK_MATCH_CACHE_DIRECTORY
            / f"{safe_match_id}.json"
        )

    @staticmethod
    def _checkpoint_signature(
        *,
        benchmark_id: str,
        target_valid_players: int,
        matches_per_player: int,
        minimum_valid_matches: int,
        target_set_number: int,
        target_set_core_name: str,
        queue: str,
    ) -> dict[str, Any]:
        return {
            "checkpoint_version": (
                CHECKPOINT_VERSION
            ),
            "benchmark_id": (
                benchmark_id
                .strip()
                .lower()
            ),
            "target_valid_players": (
                target_valid_players
            ),
            "matches_per_player": (
                matches_per_player
            ),
            "minimum_valid_matches": (
                minimum_valid_matches
            ),
            "target_set_number": (
                target_set_number
            ),
            "target_set_core_name": (
                target_set_core_name.strip()
            ),
            "queue": (
                queue.strip().upper()
            ),
        }

    @staticmethod
    def _checkpoint_paths(
        *,
        signature: dict[str, Any],
    ) -> tuple[Path, Path]:
        """
        Gera caminhos isolados por configuração de coleta.

        Exemplo:
            novice_TFTSet18_min5_max30_players100_v2.pkl

        Assim uma execução min30 nunca sobrescreve o progresso min5.
        """

        safe_benchmark = (
            str(signature["benchmark_id"])
            .strip()
            .lower()
            .replace("/", "_")
            .replace("\\", "_")
        )

        safe_set = (
            str(signature["target_set_core_name"])
            .strip()
            .replace("/", "_")
            .replace("\\", "_")
        )

        minimum_valid_matches = int(
            signature["minimum_valid_matches"]
        )
        matches_per_player = int(
            signature["matches_per_player"]
        )
        target_valid_players = int(
            signature["target_valid_players"]
        )
        checkpoint_version = int(
            signature["checkpoint_version"]
        )

        stem = (
            f"{safe_benchmark}_"
            f"{safe_set}_"
            f"min{minimum_valid_matches}_"
            f"max{matches_per_player}_"
            f"players{target_valid_players}_"
            f"v{checkpoint_version}"
        )

        return (
            BENCHMARK_CHECKPOINT_DIRECTORY
            / f"{stem}.pkl",
            BENCHMARK_CHECKPOINT_DIRECTORY
            / f"{stem}.json",
        )

    def _load_player_checkpoint(
        self,
        *,
        expected_signature: dict[str, Any],
    ) -> tuple[
        list[tuple[str, PlayerMetrics]],
        list[BenchmarkPlayerCatalogEntry],
        set[str],
        bool,
    ]:
        (
            checkpoint_path,
            _,
        ) = self._checkpoint_paths(
            signature=expected_signature,
        )

        print(
            "Checkpoint ativo    : "
            f"{checkpoint_path.name}"
        )

        if not checkpoint_path.exists():
            return (
                [],
                [],
                set(),
                False,
            )

        try:
            with checkpoint_path.open(
                "rb"
            ) as handle:
                payload = pickle.load(
                    handle
                )

        except (
            OSError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            ModuleNotFoundError,
        ) as error:
            print(
                "Checkpoint não pôde ser "
                "restaurado e será ignorado: "
                f"{error}"
            )
            return (
                [],
                [],
                set(),
                False,
            )

        if not isinstance(
            payload,
            dict,
        ):
            return (
                [],
                [],
                set(),
                False,
            )

        if (
            payload.get("signature")
            != expected_signature
        ):
            print(
                "Checkpoint encontrado, mas a assinatura "
                "não corresponde à configuração atual."
            )
            return (
                [],
                [],
                set(),
                False,
            )

        collected_metrics = (
            payload.get(
                "collected_metrics",
                [],
            )
        )

        player_catalog = (
            payload.get(
                "player_catalog",
                [],
            )
        )

        accepted_puuids = set(
            str(value)
            for value in payload.get(
                "accepted_puuids",
                [],
            )
            if str(value).strip()
        )

        if not isinstance(
            collected_metrics,
            list,
        ):
            collected_metrics = []

        if not isinstance(
            player_catalog,
            list,
        ):
            player_catalog = []

        return (
            collected_metrics,
            player_catalog,
            accepted_puuids,
            bool(payload.get("complete", False)),
        )

    def _save_player_checkpoint(
        self,
        *,
        signature: dict[str, Any],
        collected_metrics: list[
            tuple[str, PlayerMetrics]
        ],
        player_catalog: list[
            BenchmarkPlayerCatalogEntry
        ],
        accepted_puuids: set[str],
        complete: bool,
    ) -> None:
        (
            checkpoint_path,
            status_path,
        ) = self._checkpoint_paths(
            signature=signature,
        )

        checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "signature": signature,
            "collected_metrics": (
                collected_metrics
            ),
            "player_catalog": (
                player_catalog
            ),
            "accepted_puuids": sorted(
                accepted_puuids
            ),
            "complete": complete,
            "updated_at": utc_now_iso(),
        }

        temporary_pickle = (
            checkpoint_path.with_suffix(
                ".pkl.tmp"
            )
        )

        with temporary_pickle.open(
            "wb"
        ) as handle:
            pickle.dump(
                payload,
                handle,
                protocol=pickle.HIGHEST_PROTOCOL,
            )

        temporary_pickle.replace(
            checkpoint_path
        )

        status_payload = {
            "signature": signature,
            "players_saved": len(
                collected_metrics
            ),
            "catalog_entries_saved": len(
                player_catalog
            ),
            "complete": complete,
            "updated_at": payload[
                "updated_at"
            ],
            "checkpoint_path": str(
                checkpoint_path
            ),
        }

        temporary_status = (
            status_path.with_suffix(
                ".json.tmp"
            )
        )

        temporary_status.write_text(
            json.dumps(
                status_payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_status.replace(
            status_path
        )

    @staticmethod
    def _is_target_set_match(
        *,
        match_data: dict[str, Any],
        target_set_number: int,
        target_set_core_name: str,
    ) -> bool:
        info = match_data.get(
            "info"
        )

        if not isinstance(
            info,
            dict,
        ):
            return False

        raw_set_number = info.get(
            "tft_set_number"
        )

        raw_core_name = info.get(
            "tft_set_core_name"
        )

        set_number: int | None = None

        try:
            if (
                raw_set_number
                is not None
            ):
                set_number = int(
                    raw_set_number
                )
        except (
            TypeError,
            ValueError,
        ):
            set_number = None

        core_name = str(
            raw_core_name or ""
        ).strip()

        if (
            set_number
            is not None
        ):
            return (
                set_number
                == target_set_number
            )

        if core_name:
            return (
                core_name.casefold()
                == target_set_core_name
                .strip()
                .casefold()
            )

        return False

    def _resolve_player_identifier(
        self,
        *,
        player: LeaguePlayer,
    ) -> str:
        try:
            return (
                self.riot_client
                .get_player_name(
                    puuid=player.puuid,
                )
            )

        except (
            RuntimeError,
            ValueError,
            KeyError,
        ):
            return (
                f"{player.rank_label}_"
                f"{player.puuid[:12]}"
            )

    def _build_catalog_entry(
        self,
        *,
        benchmark_id: str,
        player: LeaguePlayer,
        player_metrics: PlayerMetrics,
        queue: str,
    ) -> BenchmarkPlayerCatalogEntry:
        account: dict = {}

        try:
            account = (
                self.riot_client
                .get_account_by_puuid(
                    puuid=player.puuid,
                )
            )
        except (
            RuntimeError,
            ValueError,
            KeyError,
        ):
            pass

        game_name = account.get(
            "gameName"
        )

        tag_line = account.get(
            "tagLine"
        )

        if (
            not isinstance(
                game_name,
                str,
            )
            or not game_name.strip()
        ):
            game_name = None

        if (
            not isinstance(
                tag_line,
                str,
            )
            or not tag_line.strip()
        ):
            tag_line = None

        now = utc_now_iso()

        return BenchmarkPlayerCatalogEntry(
            benchmark_id=(
                benchmark_id
                .strip()
                .lower()
            ),
            puuid=player.puuid,
            game_name=game_name,
            tag_line=tag_line,
            queue_type=(
                queue
                .strip()
                .upper()
            ),
            tier_at_collection=(
                player.tier
            ),
            division_at_collection=(
                player.division
            ),
            league_points_at_collection=(
                player.league_points
            ),
            current_tier=(
                player.tier
            ),
            current_division=(
                player.division
            ),
            current_league_points=(
                player.league_points
            ),
            matches_used=(
                player_metrics
                .general
                .matches_played
            ),
            metrics=metrics_to_dict(
                player_metrics
            ),
            collected_at=now,
            rank_checked_at=now,
            rank_history=(
                {
                    "checked_at": now,
                    "tier": player.tier,
                    "division": (
                        player.division
                    ),
                    "league_points": (
                        player.league_points
                    ),
                },
            ),
        )

    @staticmethod
    def _validate_collection_parameters(
        *,
        target_valid_players: int,
        matches_per_player: int,
        match_scan_limit: int,
        minimum_valid_matches: int,
        target_set_number: int,
        target_set_core_name: str,
        queue: str,
    ) -> None:
        if (
            target_valid_players
            < 1
        ):
            raise ValueError(
                "A meta de jogadores deve "
                "ser maior que zero."
            )

        if (
            matches_per_player
            < 1
        ):
            raise ValueError(
                "A quantidade de partidas "
                "deve ser maior que zero."
            )

        if (
            match_scan_limit
            < matches_per_player
        ):
            raise ValueError(
                "O scan de partidas não pode "
                "ser menor que matches_per_player."
            )

        if (
            minimum_valid_matches
            < 1
        ):
            raise ValueError(
                "O mínimo de partidas válidas "
                "deve ser maior que zero."
            )

        if (
            minimum_valid_matches
            > matches_per_player
        ):
            raise ValueError(
                "O mínimo de partidas válidas não "
                "pode ser maior que a quantidade "
                "de partidas solicitadas."
            )

        if (
            target_set_number
            < 1
        ):
            raise ValueError(
                "O número do Set alvo deve "
                "ser maior que zero."
            )

        if not (
            target_set_core_name.strip()
        ):
            raise ValueError(
                "O nome do Set alvo deve "
                "ser informado."
            )

        if not queue.strip():
            raise ValueError(
                "A fila do ranking deve "
                "ser informada."
            )
