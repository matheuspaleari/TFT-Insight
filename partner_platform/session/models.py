from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PlayerSession:
    game_name: str
    tag_line: str
    region: str = "BR1"
    match_count: int = 20
    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )
    analysis_report: dict[str, Any] | None = None
    benchmark_report: dict[str, Any] | None = None

    @property
    def riot_id(self) -> str:
        return f"{self.game_name} #{self.tag_line}"

    def identity_dict(self) -> dict[str, Any]:
        return {
            "game_name": self.game_name,
            "tag_line": self.tag_line,
            "region": self.region,
            "match_count": self.match_count,
            "updated_at": self.updated_at,
        }
