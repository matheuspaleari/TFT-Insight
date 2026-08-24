from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import monotonic, perf_counter
from typing import Any

from src.coaching_engine import (
    HistoricalFilter,
    HistoricalMatchRepository,
)
from src.performance_engine.models import Match
from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer


@dataclass(slots=True, frozen=True)
class MatchLoadResult:
    matches: list[Match]
    payloads: list[dict[str, Any]]
    match_ids_received: int
    cached_matches_used: int
    new_matches_downloaded: int
    failed_matches: int
    candidate_ids_considered: int = 0
    elapsed_seconds: float = 0.0
    stopped_after_target: bool = False

    @property
    def cache_hit_rate(self) -> float:
        total = (
            self.cached_matches_used
            + self.new_matches_downloaded
        )

        if total <= 0:
            return 0.0

        return round(
            self.cached_matches_used
            / total
            * 100.0,
            2,
        )


class CachedMatchService:
    """
    Cache persistente + cache curto em memória.

    Roadmap 21:
    - Riot ID -> PUUID: cache de 10 min.
    - Lista de match IDs: cache de 45 s.
    - Early-stop ao atingir a quantidade válida solicitada.
    - O histórico persistente continua em data/history/matches.jsonl.
    """

    ACCOUNT_CACHE_TTL_SECONDS = 600
    MATCH_IDS_CACHE_TTL_SECONDS = 45

    _account_cache: dict[
        tuple[str, str],
        tuple[float, str],
    ] = {}

    _match_ids_cache: dict[
        tuple[str, int],
        tuple[float, tuple[str, ...]],
    ] = {}

    _cache_lock = RLock()

    def __init__(
        self,
        *,
        project_root: Path,
        riot_client: RiotClient | None = None,
    ) -> None:
        self.project_root = project_root
        self.riot_client = riot_client or RiotClient()
        self.repository = HistoricalMatchRepository(
            project_root
            / "data"
            / "history"
            / "matches.jsonl"
        )

    @classmethod
    def clear_memory_cache(
        cls,
    ) -> None:
        """
        Limpa somente caches em memória.
        Não remove histórico persistido.
        """
        with cls._cache_lock:
            cls._account_cache.clear()
            cls._match_ids_cache.clear()

    @staticmethod
    def _is_fresh(
        stored_at: float,
        ttl_seconds: float,
    ) -> bool:
        return (
            monotonic()
            - stored_at
            <= ttl_seconds
        )

    def resolve_puuid(
        self,
        *,
        puuid: str | None,
        game_name: str | None,
        tag_line: str | None,
    ) -> str:
        if puuid and puuid.strip():
            return puuid.strip()

        if not game_name or not tag_line:
            raise ValueError(
                "Informe puuid ou game_name + tag_line."
            )

        normalized_name = game_name.strip()
        normalized_tag = tag_line.strip()

        cache_key = (
            normalized_name.lower(),
            normalized_tag.lower(),
        )

        with self._cache_lock:
            cached = self._account_cache.get(
                cache_key
            )

            if (
                cached is not None
                and self._is_fresh(
                    cached[0],
                    self.ACCOUNT_CACHE_TTL_SECONDS,
                )
            ):
                return cached[1]

        account = self.riot_client.get_account(
            game_name=normalized_name,
            tag_line=normalized_tag,
        )

        resolved = str(
            account.get(
                "puuid",
                "",
            )
        ).strip()

        if not resolved:
            raise RuntimeError(
                "A Riot API não retornou um PUUID válido."
            )

        with self._cache_lock:
            self._account_cache[
                cache_key
            ] = (
                monotonic(),
                resolved,
            )

        return resolved

    def _get_match_ids_cached(
        self,
        *,
        puuid: str,
        count: int,
    ) -> list[str]:
        cache_key = (
            puuid,
            count,
        )

        with self._cache_lock:
            cached = self._match_ids_cache.get(
                cache_key
            )

            if (
                cached is not None
                and self._is_fresh(
                    cached[0],
                    self.MATCH_IDS_CACHE_TTL_SECONDS,
                )
            ):
                return list(
                    cached[1]
                )

        match_ids = self.riot_client.get_match_ids(
            puuid=puuid,
            count=count,
        )

        normalized = tuple(
            str(match_id).strip()
            for match_id in match_ids
            if str(match_id).strip()
        )

        with self._cache_lock:
            self._match_ids_cache[
                cache_key
            ] = (
                monotonic(),
                normalized,
            )

        return list(
            normalized
        )

    def _cached_payloads_by_id(
        self,
        *,
        puuid: str,
    ) -> dict[str, dict[str, Any]]:
        cached_records = self.repository.load(
            puuid=puuid,
            historical_filter=HistoricalFilter(
                limit=None
            ),
        )

        result: dict[
            str,
            dict[str, Any],
        ] = {}

        for record in cached_records:
            match_id = str(
                record.get(
                    "match_id",
                    "",
                )
                or ""
            ).strip()

            payload = record.get(
                "payload"
            )

            if (
                match_id
                and isinstance(
                    payload,
                    dict,
                )
            ):
                result[
                    match_id
                ] = payload

        return result

    @staticmethod
    def _transform(
        *,
        payload: dict[str, Any],
        puuid: str,
    ) -> Match:
        return MatchTransformer.transform(
            match_data=payload,
            puuid=puuid,
        )

    def load_player_matches_target(
        self,
        *,
        puuid: str,
        target_count: int,
        candidate_count: int | None = None,
    ) -> MatchLoadResult:
        """
        Percorre candidatos em ordem e para quando encontra target_count
        partidas válidas. Os candidatos extras só são usados quando uma
        partida falha no download ou transformação.
        """
        started = perf_counter()

        if target_count < 1:
            raise ValueError(
                "target_count deve ser maior que zero."
            )

        effective_candidate_count = max(
            target_count,
            (
                candidate_count
                if candidate_count is not None
                else target_count
            ),
        )

        match_ids = self._get_match_ids_cached(
            puuid=puuid,
            count=effective_candidate_count,
        )

        cached_by_id = self._cached_payloads_by_id(
            puuid=puuid
        )

        matches: list[Match] = []
        payloads: list[dict[str, Any]] = []
        cached_used = 0
        downloaded = 0
        failed = 0
        considered = 0

        for match_id in match_ids:
            if len(matches) >= target_count:
                break

            considered += 1

            payload = cached_by_id.get(
                match_id
            )

            from_cache = (
                payload is not None
            )

            if payload is None:
                try:
                    payload = (
                        self.riot_client.get_match_details(
                            match_id=match_id
                        )
                    )

                    self.repository.save_raw_match(
                        match_id=match_id,
                        puuid=puuid,
                        payload=payload,
                    )

                    cached_by_id[
                        match_id
                    ] = payload

                    downloaded += 1

                except (
                    RuntimeError,
                    ValueError,
                    KeyError,
                ):
                    failed += 1
                    continue

            try:
                transformed = self._transform(
                    payload=payload,
                    puuid=puuid,
                )
            except (
                RuntimeError,
                ValueError,
                KeyError,
            ):
                failed += 1
                continue

            if from_cache:
                cached_used += 1

            payloads.append(
                payload
            )
            matches.append(
                transformed
            )

        return MatchLoadResult(
            matches=matches,
            payloads=payloads,
            match_ids_received=len(
                match_ids
            ),
            cached_matches_used=cached_used,
            new_matches_downloaded=downloaded,
            failed_matches=failed,
            candidate_ids_considered=considered,
            elapsed_seconds=round(
                perf_counter()
                - started,
                3,
            ),
            stopped_after_target=(
                len(matches) >= target_count
                and considered < len(match_ids)
            ),
        )

    def load_matches_by_ids(
        self,
        *,
        puuid: str,
        match_ids: tuple[str, ...] | list[str],
    ) -> MatchLoadResult:
        started = perf_counter()

        requested_ids = tuple(
            str(match_id).strip()
            for match_id in match_ids
            if str(match_id).strip()
        )

        if not requested_ids:
            raise ValueError(
                "É necessário informar ao menos um match_id."
            )

        if len(set(requested_ids)) != len(requested_ids):
            raise ValueError(
                "match_ids não pode conter IDs duplicados."
            )

        cached_by_id = self._cached_payloads_by_id(
            puuid=puuid
        )

        payload_by_id: dict[
            str,
            dict[str, Any],
        ] = {}

        cached_used = 0
        downloaded = 0
        failed = 0

        for match_id in requested_ids:
            payload = cached_by_id.get(
                match_id
            )

            if payload is not None:
                payload_by_id[
                    match_id
                ] = payload
                cached_used += 1
                continue

            try:
                payload = (
                    self.riot_client.get_match_details(
                        match_id=match_id
                    )
                )

                self.repository.save_raw_match(
                    match_id=match_id,
                    puuid=puuid,
                    payload=payload,
                )

                payload_by_id[
                    match_id
                ] = payload

                downloaded += 1

            except (
                RuntimeError,
                ValueError,
                KeyError,
            ):
                failed += 1

        payloads: list[dict[str, Any]] = []
        matches: list[Match] = []

        for match_id in requested_ids:
            payload = payload_by_id.get(
                match_id
            )

            if payload is None:
                continue

            try:
                transformed = self._transform(
                    payload=payload,
                    puuid=puuid,
                )
            except (
                RuntimeError,
                ValueError,
                KeyError,
            ):
                failed += 1
                continue

            payloads.append(
                payload
            )
            matches.append(
                transformed
            )

        return MatchLoadResult(
            matches=matches,
            payloads=payloads,
            match_ids_received=len(
                requested_ids
            ),
            cached_matches_used=cached_used,
            new_matches_downloaded=downloaded,
            failed_matches=failed,
            candidate_ids_considered=len(
                requested_ids
            ),
            elapsed_seconds=round(
                perf_counter()
                - started,
                3,
            ),
            stopped_after_target=False,
        )

    def load_player_matches(
        self,
        *,
        puuid: str,
        count: int,
    ) -> MatchLoadResult:
        """
        Compatibilidade com chamadas antigas.
        """
        return self.load_player_matches_target(
            puuid=puuid,
            target_count=count,
            candidate_count=count,
        )
