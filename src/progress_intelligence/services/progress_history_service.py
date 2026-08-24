from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models.progress_snapshot import ProgressSnapshot


class ProgressHistoryService:
    """Append-only persistence for long-term player progress."""

    FILE_NAME = "progress_history.json"

    @classmethod
    def path_for(cls, *, player_directory: Path) -> Path:
        return Path(player_directory) / "learning" / cls.FILE_NAME

    @classmethod
    def load(cls, *, player_directory: Path) -> list[ProgressSnapshot]:
        path = cls.path_for(player_directory=player_directory)
        if not path.exists():
            return []

        payload = json.loads(path.read_text(encoding="utf-8"))
        return [
            ProgressSnapshot.from_dict(item)
            for item in list(payload.get("snapshots") or [])
        ]

    @classmethod
    def append(
        cls,
        *,
        player_directory: Path,
        snapshot: ProgressSnapshot,
    ) -> bool:
        path = cls.path_for(player_directory=player_directory)
        path.parent.mkdir(parents=True, exist_ok=True)
        history = cls.load(player_directory=player_directory)

        if any(item.snapshot_id == snapshot.snapshot_id for item in history):
            return False

        history.append(snapshot)
        payload: dict[str, Any] = {
            "schema_version": 1,
            "snapshots": [item.to_dict() for item in history],
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
