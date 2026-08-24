"""
Histórico de observações de elo do TFT Insight.

A integração registra o elo observado no momento da análise e mede
quantas partidas novas apareceram desde o último ponto de corte.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.riot_client import RiotClient
from src.storage import PlayerRepository


class RankObservationService:
    FILE_NAME = "rank_observations.json"
    QUEUE_TYPE = "RANKED_TFT"
    DEFAULT_SCAN_LIMIT = 100

    def __init__(
        self,
        riot_client: RiotClient | None = None,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.riot_client = riot_client or RiotClient()
        self.player_repository = player_repository or PlayerRepository()

    def observe(
        self,
        *,
        game_name: str,
        tag_line: str,
        scan_limit: int = DEFAULT_SCAN_LIMIT,
    ) -> dict[str, Any]:
        """Consulta Riot + registra a observação. Mantido para diagnóstico manual."""
        account = self.riot_client.get_account(
            game_name=game_name,
            tag_line=tag_line,
        )
        puuid = str(account.get("puuid", "")).strip()
        if not puuid:
            raise RuntimeError("A Riot API não retornou um PUUID válido.")

        canonical_name = str(account.get("gameName", game_name))
        canonical_tag = str(account.get("tagLine", tag_line))

        ranked_entry = self.riot_client.get_ranked_tft_entry(
            puuid=puuid,
            queue_type=self.QUEUE_TYPE,
        )
        match_ids = self.riot_client.get_match_ids(
            puuid=puuid,
            count=scan_limit,
        )

        return self.record_resolved(
            puuid=puuid,
            game_name=canonical_name,
            tag_line=canonical_tag,
            ranked_entry=ranked_entry,
            current_match_ids=match_ids,
            scan_limit=scan_limit,
        )

    def record_resolved(
        self,
        *,
        puuid: str,
        game_name: str,
        tag_line: str,
        ranked_entry: dict[str, Any] | None,
        current_match_ids: list[str],
        scan_limit: int,
    ) -> dict[str, Any]:
        """
        Registra usando dados que o PlayerAnalysisService já consultou.

        Assim o fluxo normal não duplica Account-V1, League-V1 e Match IDs.
        """
        player_directory = self.player_repository.ensure_player(
            puuid=puuid,
            game_name=game_name,
            tag_line=tag_line,
        )
        history = self._load(player_directory)
        previous = history["observations"][-1] if history["observations"] else None

        new_match_ids, association = self._resolve_new_matches(
            current_match_ids=current_match_ids,
            previous=previous,
        )

        candidate = {
            "queue_type": self.QUEUE_TYPE,
            "ranked": ranked_entry is not None,
            "tier": self._text(ranked_entry, "tier"),
            "division": self._text(ranked_entry, "rank"),
            "league_points": self._int(ranked_entry, "leaguePoints"),
            "wins": self._int(ranked_entry, "wins"),
            "losses": self._int(ranked_entry, "losses"),
            "latest_match_id": (
                current_match_ids[0]
                if current_match_ids
                else None
            ),
            "previous_latest_match_id": (
                previous.get("latest_match_id")
                if previous
                else None
            ),
            "matches_since_previous_rank_snapshot": len(new_match_ids),
            "new_match_ids": new_match_ids,
            "first_new_match_id": new_match_ids[-1] if new_match_ids else None,
            "last_new_match_id": new_match_ids[0] if new_match_ids else None,
            "association": association,
            "scan_limit": scan_limit,
        }

        # Evita criar snapshots idênticos quando o usuário apenas recarrega a análise.
        if previous and self._same_state(previous, candidate):
            return {
                "player_directory": str(player_directory),
                "history_path": str(self._path(player_directory)),
                "observation": previous,
                "previous_observation": (
                    history["observations"][-2]
                    if len(history["observations"]) >= 2
                    else None
                ),
                "total_observations": len(history["observations"]),
                "persisted_now": False,
            }

        observation = {
            "observation_id": self._observation_id(),
            "observed_at": datetime.now(timezone.utc).isoformat(),
            **candidate,
        }

        history["player"] = {
            "puuid": puuid,
            "game_name": game_name,
            "tag_line": tag_line,
        }
        history["observations"].append(observation)
        self._save(player_directory, history)

        return {
            "player_directory": str(player_directory),
            "history_path": str(self._path(player_directory)),
            "observation": observation,
            "previous_observation": previous,
            "total_observations": len(history["observations"]),
            "persisted_now": True,
        }

    @staticmethod
    def _same_state(
        previous: dict[str, Any],
        candidate: dict[str, Any],
    ) -> bool:
        keys = (
            "ranked",
            "tier",
            "division",
            "league_points",
            "latest_match_id",
        )
        return all(
            previous.get(key) == candidate.get(key)
            for key in keys
        )

    @staticmethod
    def _resolve_new_matches(
        *,
        current_match_ids: list[str],
        previous: dict[str, Any] | None,
    ) -> tuple[list[str], str]:
        if previous is None:
            return [], "BASELINE"

        previous_latest = previous.get("latest_match_id")
        if not previous_latest:
            return [], "BASELINE"

        if not current_match_ids:
            return [], "NO_MATCHES"

        if current_match_ids[0] == previous_latest:
            return [], "NO_NEW_MATCHES"

        try:
            previous_index = current_match_ids.index(previous_latest)
        except ValueError:
            return list(current_match_ids), "TRUNCATED"

        new_match_ids = current_match_ids[:previous_index]

        if len(new_match_ids) == 1:
            return new_match_ids, "EXACT"
        if len(new_match_ids) > 1:
            return new_match_ids, "INTERVAL"
        return [], "NO_NEW_MATCHES"

    @classmethod
    def _path(cls, player_directory: Path) -> Path:
        path = player_directory / "history" / cls.FILE_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def _load(cls, player_directory: Path) -> dict[str, Any]:
        path = cls._path(player_directory)
        if not path.exists():
            return {"schema_version": 1, "player": {}, "observations": []}

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 1, "player": {}, "observations": []}

        if not isinstance(data, dict):
            return {"schema_version": 1, "player": {}, "observations": []}

        observations = data.get("observations")
        if not isinstance(observations, list):
            observations = []

        return {
            "schema_version": 1,
            "player": data.get("player", {}),
            "observations": observations,
        }

    @classmethod
    def _save(cls, player_directory: Path, data: dict[str, Any]) -> None:
        path = cls._path(player_directory)
        temp = path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(path)

    @staticmethod
    def _observation_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return f"rank_{stamp}"

    @staticmethod
    def _text(entry: dict[str, Any] | None, key: str) -> str | None:
        if not entry:
            return None
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            return None
        return value.strip().upper()

    @staticmethod
    def _int(entry: dict[str, Any] | None, key: str) -> int | None:
        if not entry:
            return None
        value = entry.get(key)
        return value if isinstance(value, int) else None
