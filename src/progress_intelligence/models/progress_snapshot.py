from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ProgressSnapshot:
    snapshot_id: str
    created_at: str
    priority_skill_id: str | None
    skills: dict[str, dict[str, Any]]
    archived_cycles_total: int
    source: str = "learning_profile"
    schema_version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "priority_skill_id": self.priority_skill_id,
            "archived_cycles_total": self.archived_cycles_total,
            "source": self.source,
            "skills": self.skills,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProgressSnapshot":
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            snapshot_id=str(data["snapshot_id"]),
            created_at=str(data["created_at"]),
            priority_skill_id=data.get("priority_skill_id"),
            archived_cycles_total=int(data.get("archived_cycles_total", 0)),
            source=str(data.get("source", "learning_profile")),
            skills=dict(data.get("skills") or {}),
            metadata=dict(data.get("metadata") or {}),
        )
