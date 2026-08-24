from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

import streamlit as st

from .models import PlayerSession


class PlayerSessionStore:
    CURRENT_KEY = "tft_current_player_session"
    HISTORY_KEY = "tft_recent_player_sessions"
    MAX_HISTORY = 5

    @classmethod
    def current(cls) -> PlayerSession | None:
        value = st.session_state.get(
            cls.CURRENT_KEY
        )

        if isinstance(value, PlayerSession):
            return value

        if isinstance(value, dict):
            try:
                return PlayerSession(**value)
            except TypeError:
                return None

        return None

    @classmethod
    def current_defaults(
        cls,
        *,
        fallback_name: str = "Pinador doss",
        fallback_tag: str = "000",
        fallback_matches: int = 20,
    ) -> tuple[str, str, int]:
        current = cls.current()

        if current is None:
            return (
                fallback_name,
                fallback_tag,
                fallback_matches,
            )

        return (
            current.game_name,
            current.tag_line,
            current.match_count,
        )

    @classmethod
    def set_player(
        cls,
        *,
        game_name: str,
        tag_line: str,
        region: str = "BR1",
        match_count: int = 20,
    ) -> PlayerSession:
        normalized_name = game_name.strip()
        normalized_tag = (
            tag_line.strip().lstrip("#")
        )
        normalized_region = region.strip() or "BR1"

        existing = cls.current()

        same_player = (
            existing is not None
            and existing.game_name.lower()
            == normalized_name.lower()
            and existing.tag_line.lower()
            == normalized_tag.lower()
            and existing.region.lower()
            == normalized_region.lower()
        )

        session = PlayerSession(
            game_name=normalized_name,
            tag_line=normalized_tag,
            region=normalized_region,
            match_count=match_count,
            analysis_report=(
                existing.analysis_report
                if same_player
                else None
            ),
            benchmark_report=(
                existing.benchmark_report
                if same_player
                else None
            ),
        )

        st.session_state[
            cls.CURRENT_KEY
        ] = session

        cls._push_history(
            session
        )

        return session

    @classmethod
    def save_analysis(
        cls,
        report: dict[str, Any],
        *,
        game_name: str,
        tag_line: str,
        region: str = "BR1",
        match_count: int = 20,
    ) -> PlayerSession:
        session = cls.set_player(
            game_name=game_name,
            tag_line=tag_line,
            region=region,
            match_count=match_count,
        )

        session.analysis_report = deepcopy(
            report
        )
        session.updated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        st.session_state[
            cls.CURRENT_KEY
        ] = session

        cls._push_history(
            session
        )

        return session

    @classmethod
    def save_benchmark(
        cls,
        report: dict[str, Any],
    ) -> PlayerSession | None:
        session = cls.current()

        if session is None:
            return None

        session.benchmark_report = deepcopy(
            report
        )
        session.updated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        st.session_state[
            cls.CURRENT_KEY
        ] = session

        cls._push_history(
            session
        )

        return session

    @classmethod
    def recent(
        cls,
    ) -> list[dict[str, Any]]:
        value = st.session_state.get(
            cls.HISTORY_KEY,
            [],
        )

        if not isinstance(
            value,
            list,
        ):
            return []

        return list(value)

    @classmethod
    def restore(
        cls,
        index: int,
    ) -> PlayerSession | None:
        history = cls.recent()

        if not (
            0 <= index < len(history)
        ):
            return None

        item = history[index]

        session = PlayerSession(
            game_name=item["game_name"],
            tag_line=item["tag_line"],
            region=item.get(
                "region",
                "BR1",
            ),
            match_count=int(
                item.get(
                    "match_count",
                    20,
                )
            ),
        )

        st.session_state[
            cls.CURRENT_KEY
        ] = session

        return session

    @classmethod
    def clear(
        cls,
    ) -> None:
        st.session_state.pop(
            cls.CURRENT_KEY,
            None,
        )

    @classmethod
    def _push_history(
        cls,
        session: PlayerSession,
    ) -> None:
        history = [
            item
            for item in cls.recent()
            if not (
                item.get(
                    "game_name",
                    "",
                ).lower()
                == session.game_name.lower()
                and item.get(
                    "tag_line",
                    "",
                ).lower()
                == session.tag_line.lower()
            )
        ]

        history.insert(
            0,
            session.identity_dict(),
        )

        st.session_state[
            cls.HISTORY_KEY
        ] = history[
            : cls.MAX_HISTORY
        ]
