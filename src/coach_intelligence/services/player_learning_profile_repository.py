from __future__ import annotations

from typing import Any


class PlayerLearningProfileRepository:
    """
    Usa o PlayerRepository existente sem alterar seu contrato.
    """

    def __init__(
        self,
        *,
        player_repository,
    ) -> None:
        self.player_repository = (
            player_repository
        )

    def load(
        self,
        *,
        puuid: str,
    ) -> dict[str, Any] | None:
        path = (
            self.player_repository
            .get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "learning_profile.json"
        )

        data = (
            self.player_repository._read_json(
                path=path
            )
        )

        return (
            data
            if isinstance(
                data,
                dict,
            )
            else None
        )

    def save(
        self,
        *,
        puuid: str,
        profile: dict[str, Any],
    ):
        path = (
            self.player_repository
            .get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "learning_profile.json"
        )

        previous = self.load(
            puuid=puuid
        )

        payload = dict(
            profile
        )

        if previous:
            history = list(
                previous.get(
                    "snapshots",
                    [],
                )
            )

            previous_snapshot = {
                key: value
                for key, value
                in previous.items()
                if key != "snapshots"
            }

            history.insert(
                0,
                previous_snapshot,
            )

            payload[
                "snapshots"
            ] = history[:20]
        else:
            payload[
                "snapshots"
            ] = []

        self.player_repository._write_json(
            path=path,
            data=payload,
        )

        return path
