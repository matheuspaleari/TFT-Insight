"""
Coleta e construção de benchmarks por grupo competitivo.
"""

from __future__ import annotations

import time

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


class BenchmarkCollector:
    """
    Coleta partidas de jogadores pertencentes a um grupo competitivo.

    O Collector:

    - obtém candidatos pelo LeaguePlayerProvider;
    - processa as partidas de cada candidato;
    - descarta jogadores com amostra insuficiente;
    - continua até atingir a meta de jogadores válidos;
    - consolida as métricas em um Benchmark.

    Ele não possui regras fixas de elo. Toda a configuração vem de
    BenchmarkGroupConfiguration.
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
        """
        Constrói um benchmark para o grupo informado.

        Args:
            benchmark_id: Identificador do grupo competitivo.
            queue: Fila ranqueada usada na coleta.
            minimum_valid_matches: Quantidade mínima de partidas válidas
                exigida por jogador. Quando omitida, exige todas as
                partidas configuradas para o grupo.
        """

        started_at = time.monotonic()

        configuration = (
            get_benchmark_group_configuration(
                benchmark_id
            )
        )

        matches_per_player = (
            configuration.matches_per_player
        )

        required_valid_matches = (
            matches_per_player
            if minimum_valid_matches is None
            else minimum_valid_matches
        )

        self._validate_collection_parameters(
            target_valid_players=(
                configuration.target_valid_players
            ),
            matches_per_player=matches_per_player,
            minimum_valid_matches=(
                required_valid_matches
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
            f"Partidas solicitadas: "
            f"{matches_per_player}"
        )
        print(
            f"Mínimo válido       : "
            f"{required_valid_matches}"
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

        Returns:
            Lista contendo identificador do jogador e PlayerMetrics.
        """

        configuration = (
            get_benchmark_group_configuration(
                benchmark_id
            )
        )

        self.last_player_catalog = []

        matches_per_player = (
            configuration.matches_per_player
        )

        required_valid_matches = (
            matches_per_player
            if minimum_valid_matches is None
            else minimum_valid_matches
        )

        self._validate_collection_parameters(
            target_valid_players=(
                configuration.target_valid_players
            ),
            matches_per_player=matches_per_player,
            minimum_valid_matches=(
                required_valid_matches
            ),
            queue=queue,
        )

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

        collected_metrics: list[
            tuple[str, PlayerMetrics]
        ] = []

        attempted_players = 0
        discarded_players = 0

        for candidate in candidates:
            if (
                len(collected_metrics)
                >= configuration.target_valid_players
            ):
                break

            attempted_players += 1

            current_valid = len(collected_metrics)

            print()
            print(
                f"[{attempted_players}/{len(candidates)}] "
                f"{candidate.rank_label} · "
                f"válidos {current_valid}/"
                f"{configuration.target_valid_players}"
            )

            player_metrics = (
                self._collect_player_metrics(
                    player=candidate,
                    matches_per_player=(
                        matches_per_player
                    ),
                    minimum_valid_matches=(
                        required_valid_matches
                    ),
                )
            )

            if player_metrics is None:
                discarded_players += 1
                print(
                    "  Descartado: amostra de partidas "
                    "válidas insuficiente."
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

            self.last_player_catalog.append(
                self._build_catalog_entry(
                    benchmark_id=benchmark_id,
                    player=candidate,
                    player_metrics=player_metrics,
                    queue=queue,
                )
            )

            print(
                "  Aceito: "
                f"{player_identifier} · "
                f"{player_metrics.general.matches_played} "
                "partidas válidas."
            )

        valid_players = len(collected_metrics)

        print()
        print("-" * 80)
        print(
            f"Candidatos tentados : "
            f"{attempted_players}"
        )
        print(
            f"Jogadores válidos   : "
            f"{valid_players}"
        )
        print(
            f"Jogadores descartados: "
            f"{discarded_players}"
        )

        if (
            valid_players
            < configuration.target_valid_players
        ):
            raise RuntimeError(
                "Não foi possível atingir a meta do benchmark "
                f"'{benchmark_id}'. "
                f"Meta: {configuration.target_valid_players}; "
                f"válidos: {valid_players}; "
                f"candidatos disponíveis: {len(candidates)}. "
                "Aumente candidate_multiplier ou reduza "
                "minimum_valid_matches."
            )

        return collected_metrics

    def _collect_player_metrics(
        self,
        *,
        player: LeaguePlayer,
        matches_per_player: int,
        minimum_valid_matches: int,
    ) -> PlayerMetrics | None:
        """
        Busca, transforma e calcula as métricas de um jogador.
        """

        try:
            match_ids = self.riot_client.get_match_ids(
                puuid=player.puuid,
                count=matches_per_player,
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
            return None

        if len(match_ids) < minimum_valid_matches:
            print(
                "  Partidas encontradas: "
                f"{len(match_ids)}/"
                f"{minimum_valid_matches} exigidas."
            )
            return None

        matches = []

        for match_index, match_id in enumerate(
            match_ids,
            start=1,
        ):
            try:
                match_data = (
                    self.riot_client.get_match_details(
                        match_id=match_id,
                    )
                )

                match = (
                    self.match_transformer.transform(
                        match_data=match_data,
                        puuid=player.puuid,
                    )
                )

                matches.append(match)

            except (
                RuntimeError,
                ValueError,
                KeyError,
            ) as error:
                print(
                    "  Partida inválida "
                    f"{match_index}/{len(match_ids)}: "
                    f"{error}"
                )

        if len(matches) < minimum_valid_matches:
            print(
                "  Partidas válidas: "
                f"{len(matches)}/"
                f"{minimum_valid_matches} exigidas."
            )
            return None

        try:
            return self.metrics_calculator.calculate(
                matches
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
            return None

    def _resolve_player_identifier(
        self,
        *,
        player: LeaguePlayer,
    ) -> str:
        """
        Tenta obter o Riot ID; usa um identificador técnico como fallback.
        """

        try:
            return self.riot_client.get_player_name(
                puuid=player.puuid,
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
            account = self.riot_client.get_account_by_puuid(
                puuid=player.puuid,
            )
        except (RuntimeError, ValueError, KeyError):
            pass

        game_name = account.get("gameName")
        tag_line = account.get("tagLine")
        if not isinstance(game_name, str) or not game_name.strip():
            game_name = None
        if not isinstance(tag_line, str) or not tag_line.strip():
            tag_line = None

        now = utc_now_iso()
        return BenchmarkPlayerCatalogEntry(
            benchmark_id=benchmark_id.strip().lower(),
            puuid=player.puuid,
            game_name=game_name,
            tag_line=tag_line,
            queue_type=queue.strip().upper(),
            tier_at_collection=player.tier,
            division_at_collection=player.division,
            league_points_at_collection=player.league_points,
            current_tier=player.tier,
            current_division=player.division,
            current_league_points=player.league_points,
            matches_used=player_metrics.general.matches_played,
            metrics=metrics_to_dict(player_metrics),
            collected_at=now,
            rank_checked_at=now,
            rank_history=({
                "checked_at": now,
                "tier": player.tier,
                "division": player.division,
                "league_points": player.league_points,
            },),
        )

    @staticmethod
    def _validate_collection_parameters(
        *,
        target_valid_players: int,
        matches_per_player: int,
        minimum_valid_matches: int,
        queue: str,
    ) -> None:
        if target_valid_players < 1:
            raise ValueError(
                "A meta de jogadores deve ser maior que zero."
            )

        if matches_per_player < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )

        if minimum_valid_matches < 1:
            raise ValueError(
                "O mínimo de partidas válidas deve ser maior que zero."
            )

        if minimum_valid_matches > matches_per_player:
            raise ValueError(
                "O mínimo de partidas válidas não pode ser maior "
                "que a quantidade de partidas solicitadas."
            )

        if not queue.strip():
            raise ValueError(
                "A fila do ranking deve ser informada."
            )
