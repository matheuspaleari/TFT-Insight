from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx


class DashboardApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        timeout: float = 90.0,
    ) -> None:
        self.base_url = (
            base_url.rstrip("/")
        )
        self.api_key = api_key
        self.timeout = timeout

    def _headers(
        self,
    ) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid4()),
        }

        if self.api_key:
            headers[
                "X-API-Key"
            ] = self.api_key

        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: (
            dict[str, Any]
            | None
        ) = None,
        params: (
            dict[str, Any]
            | None
        ) = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        with httpx.Client(
            timeout=(
                self.timeout
                if timeout is None
                else timeout
            )
        ) as client:
            response = client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=payload,
                params=params,
            )

            # Preserve the real HTTPStatusError and response body so
            # the UI can translate it into a friendly message.
            response.raise_for_status()

            return response.json()

    def health(
        self,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/health",
        )

    def analyze_player(
        self,
        *,
        game_name: str,
        tag_line: str,
        match_count: int = 20,
        learn: bool = True,
        region: str = "BR1",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/analyze/player",
            payload={
                "source": "partner",
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                    "region": region,
                },
                "match_count": match_count,
                "learn": learn,
            },
            # A análise pesada pode aguardar na fila antes de começar.
            # O timeout maior vale somente para este fluxo.
            timeout=900.0,
        )

    def queue_status(
        self,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/v1/queue/status",
            timeout=10.0,
        )


    def benchmark(
        self,
        *,
        benchmark_id: str,
        include_players: bool = True,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/benchmark/{benchmark_id}",
            params={"include_players": str(include_players).lower()},
        )

    def compare_player_to_benchmark(
        self,
        *,
        benchmark_id: str,
        game_name: str,
        tag_line: str,
        match_count: int = 20,
        region: str = "BR1",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/benchmark/{benchmark_id}/compare/player",
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                    "region": region,
                },
                "match_count": match_count,
            },
        )

    def challenger_benchmark(
        self,
        *,
        include_players: bool = True,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/v1/benchmark/challenger",
            params={
                "include_players": str(
                    include_players
                ).lower(),
            },
        )

    def compare_player_to_challenger(
        self,
        *,
        game_name: str,
        tag_line: str,
        match_count: int = 20,
        region: str = "BR1",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            (
                "/v1/benchmark/challenger/"
                "compare/player"
            ),
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                    "region": region,
                },
                "match_count": (
                    match_count
                ),
            },
        )


    def latest_post_match_report(
        self,
        *,
        game_name: str,
        tag_line: str,
        skill_id: str,
        skill_label: str,
        mission_title: str,
        objective: str,
        history_size: int = 10,
        competitive_context: dict[str, Any] | None = None,
        coach_fusion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/post-match/player/latest",
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                },
                "training": {
                    "skill_id": skill_id,
                    "skill_label": skill_label,
                    "mission_title": mission_title,
                    "objective": objective,
                },
                "history_size": history_size,
                "competitive_context": competitive_context or {},
                "coach_fusion": coach_fusion or {},
            },
        )


    def composition_intelligence(
        self,
        *,
        game_name: str,
        tag_line: str,
        match_count: int = 30,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/composition-intelligence/player/history",
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                },
                "match_count": match_count,
            },
        )


    def contest_intelligence(
        self,
        *,
        game_name: str,
        tag_line: str,
        match_count: int = 30,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/contest-intelligence/player/history",
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                },
                "match_count": match_count,
            },
        )


    def economy_intelligence(
        self,
        *,
        game_name: str,
        tag_line: str,
        match_count: int = 30,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/economy-intelligence/player/history",
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                },
                "match_count": match_count,
            },
        )

    def carry_item_intelligence(
        self,
        *,
        game_name: str,
        tag_line: str,
        match_count: int = 30,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/carry-item-intelligence/player/history",
            payload={
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                },
                "match_count": match_count,
            },
        )

