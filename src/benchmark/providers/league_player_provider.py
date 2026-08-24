"""
Provider responsável por selecionar jogadores para benchmarks.
"""

from collections.abc import Iterable
from typing import Any

from src.benchmark.group_configuration import (
    BenchmarkGroupConfiguration,
    TierSamplingRule,
    get_benchmark_group_configuration,
)
from src.benchmark.models import LeaguePlayer
from src.riot_client import RiotClient


class LeaguePlayerProvider:
    """
    Busca candidatos distribuídos entre os elos de um grupo.

    O Provider não acessa partidas nem calcula métricas.
    Sua responsabilidade é somente selecionar candidatos.
    """

    def __init__(
        self,
        riot_client: RiotClient,
    ) -> None:
        self.riot_client = riot_client

    def get_players(
        self,
        *,
        benchmark_id: str,
    ) -> list[LeaguePlayer]:
        """
        Retorna jogadores candidatos para um benchmark.

        A quantidade buscada é superior à meta de jogadores válidos,
        permitindo que o Collector descarte candidatos problemáticos.
        """

        configuration = (
            get_benchmark_group_configuration(
                benchmark_id
            )
        )

        players_by_rule: list[
            list[LeaguePlayer]
        ] = []

        seen_puuids: set[str] = set()

        for rule in configuration.sampling_rules:
            rule_players = (
                self._get_players_for_rule(
                    configuration=configuration,
                    rule=rule,
                )
            )

            unique_rule_players = []

            for player in rule_players:
                if player.puuid in seen_puuids:
                    continue

                seen_puuids.add(
                    player.puuid
                )

                unique_rule_players.append(
                    player
                )

            players_by_rule.append(
                unique_rule_players
            )

        return self._interleave_players(
            players_by_rule
        )

    def _get_players_for_rule(
        self,
        *,
        configuration: BenchmarkGroupConfiguration,
        rule: TierSamplingRule,
    ) -> list[LeaguePlayer]:
        """
        Busca candidatos suficientes para uma regra de elo.
        """

        requested_candidates = (
            self._calculate_rule_candidate_limit(
                configuration=configuration,
                rule=rule,
            )
        )

        if rule.tier in {
            "MASTER",
            "GRANDMASTER",
            "CHALLENGER",
        }:
            return self._get_apex_players(
                tier=rule.tier,
                limit=requested_candidates,
            )

        return self._get_division_players(
            tier=rule.tier,
            divisions=rule.divisions,
            limit=requested_candidates,
        )

    def _get_apex_players(
        self,
        *,
        tier: str,
        limit: int,
    ) -> list[LeaguePlayer]:
        """
        Busca jogadores Master, Grandmaster ou Challenger.
        """

        entries = (
            self.riot_client
            .get_apex_league_players(
                tier=tier,
                limit=limit,
                queue="RANKED_TFT",
            )
        )

        return self._convert_entries(
            entries=entries,
            fallback_tier=tier,
            fallback_division="I",
        )

    def _get_division_players(
        self,
        *,
        tier: str,
        divisions: tuple[str, ...],
        limit: int,
    ) -> list[LeaguePlayer]:
        """
        Busca jogadores de elos com divisão I–IV.
        """

        if not divisions:
            raise ValueError(
                f"O elo {tier} exige divisões para coleta."
            )

        collected: list[
            LeaguePlayer
        ] = []

        seen_puuids: set[str] = set()

        page = 1

        while len(collected) < limit:
            page_has_results = False

            division_results: list[
                list[LeaguePlayer]
            ] = []

            for division in divisions:
                entries = (
                    self.riot_client
                    .get_league_entries(
                        tier=tier,
                        division=division,
                        page=page,
                        queue="RANKED_TFT",
                    )
                )

                players = self._convert_entries(
                    entries=entries,
                    fallback_tier=tier,
                    fallback_division=division,
                )

                if players:
                    page_has_results = True

                division_results.append(
                    players
                )

            if not page_has_results:
                break

            interleaved_players = (
                self._interleave_players(
                    division_results
                )
            )

            for player in interleaved_players:
                if player.puuid in seen_puuids:
                    continue

                seen_puuids.add(
                    player.puuid
                )

                collected.append(
                    player
                )

                if len(collected) >= limit:
                    break

            page += 1

        return collected[:limit]

    @staticmethod
    def _calculate_rule_candidate_limit(
        *,
        configuration: BenchmarkGroupConfiguration,
        rule: TierSamplingRule,
    ) -> int:
        """
        Aplica o multiplicador de candidatos à meta do elo.
        """

        return max(
            rule.target_players,
            round(
                rule.target_players
                * configuration
                .candidate_multiplier
            ),
        )

    @staticmethod
    def _convert_entries(
        *,
        entries: Iterable[
            dict[str, Any]
        ],
        fallback_tier: str,
        fallback_division: str,
    ) -> list[LeaguePlayer]:
        """
        Converte entradas da Riot API em LeaguePlayer.
        """

        players = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            try:
                player = (
                    LeaguePlayer.from_riot_entry(
                        entry,
                        fallback_tier=(
                            fallback_tier
                        ),
                        fallback_division=(
                            fallback_division
                        ),
                    )
                )

            except ValueError:
                continue

            if player.inactive:
                continue

            players.append(player)

        return sorted(
            players,
            key=lambda player: (
                player.league_points,
                player.games_played,
            ),
            reverse=True,
        )

    @staticmethod
    def _interleave_players(
        groups: list[
            list[LeaguePlayer]
        ],
    ) -> list[LeaguePlayer]:
        """
        Intercala jogadores de diferentes elos ou divisões.

        Isso evita que o início da lista fique dominado por apenas
        um elo quando o Collector parar ao atingir a meta.
        """

        if not groups:
            return []

        interleaved = []

        maximum_length = max(
            (
                len(group)
                for group in groups
            ),
            default=0,
        )

        for index in range(maximum_length):
            for group in groups:
                if index < len(group):
                    interleaved.append(
                        group[index]
                    )

        return interleaved