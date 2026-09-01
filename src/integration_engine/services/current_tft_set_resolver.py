from __future__ import annotations

from threading import RLock
from time import monotonic
from typing import Any

from src.role_inference.clients.community_dragon_client import (
    CommunityDragonClient,
)


class CurrentTftSetResolver:
    """
    Resolve o número do set competitivo publicado no CommunityDragon.

    O resultado fica em memória por algumas horas porque a troca de set
    é rara e não deve adicionar uma chamada externa a cada análise.
    """

    CACHE_TTL_SECONDS = 21600

    _cache_lock = RLock()
    _cached_value: tuple[float, int] | None = None

    def __init__(
        self,
        *,
        client: CommunityDragonClient | None = None,
    ) -> None:
        self.client = (
            client
            or CommunityDragonClient(
                timeout_seconds=8.0
            )
        )

    @classmethod
    def clear_cache(cls) -> None:
        with cls._cache_lock:
            cls._cached_value = None

    @classmethod
    def _cached(cls) -> int | None:
        with cls._cache_lock:
            cached = cls._cached_value

            if cached is None:
                return None

            stored_at, set_number = cached

            if (
                monotonic()
                - stored_at
                > cls.CACHE_TTL_SECONDS
            ):
                cls._cached_value = None
                return None

            return set_number

    @classmethod
    def _store(
        cls,
        set_number: int,
    ) -> int:
        with cls._cache_lock:
            cls._cached_value = (
                monotonic(),
                set_number,
            )

        return set_number

    @staticmethod
    def _known_set_numbers(
        data: dict[str, Any],
    ) -> set[int]:
        result: set[int] = set()

        sets = data.get("sets")

        if isinstance(sets, dict):
            for key in sets:
                try:
                    value = int(str(key))
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if value > 0:
                    result.add(value)

        return result

    @staticmethod
    def _base_mutator_set_numbers(
        data: dict[str, Any],
    ) -> set[int]:
        result: set[int] = set()

        set_data = data.get("setData")

        if not isinstance(set_data, list):
            return result

        for item in set_data:
            if not isinstance(item, dict):
                continue

            raw_number = item.get("number")

            if not isinstance(
                raw_number,
                (int, float),
            ):
                continue

            number = int(raw_number)
            mutator = str(
                item.get(
                    "mutator",
                    "",
                )
                or ""
            ).strip()

            if (
                number > 0
                and mutator == f"TFTSet{number}"
            ):
                result.add(number)

        return result

    def resolve(self) -> int:
        cached = self._cached()

        if cached is not None:
            return cached

        data = self.client.get_tft_data(
            channel="latest",
            locale="pt_br",
        )

        known = self._known_set_numbers(
            data
        )
        base_mutators = (
            self._base_mutator_set_numbers(
                data
            )
        )

        candidates = (
            known & base_mutators
            if base_mutators
            else known
        )

        if not candidates:
            raise RuntimeError(
                "Não foi possível identificar o set atual do TFT."
            )

        return self._store(
            max(candidates)
        )

    def resolve_or_none(
        self,
    ) -> int | None:
        try:
            return self.resolve()
        except (
            RuntimeError,
            ValueError,
            KeyError,
        ):
            # O filtro ainda consegue se proteger contra mistura de sets:
            # a partida TFT válida mais recente vira a referência local.
            return None
