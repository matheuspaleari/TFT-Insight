from __future__ import annotations

import hashlib
import json
from typing import Any

from ..models.progress_snapshot import ProgressSnapshot


class ProgressSnapshotService:
    """Builds immutable long-term progress snapshots from Learning Profile output."""

    @staticmethod
    def _normalize_skill(skill: dict[str, Any]) -> dict[str, Any]:
        score = skill.get("score")
        return {
            "state": skill.get("state"),
            "score": None if score is None else float(score),
            "level": skill.get("level", "NOT_EVALUATED"),
            "trend": skill.get("trend", "INSUFFICIENT_HISTORY"),
            "trend_confidence": skill.get("trend_confidence", "LOW"),
            "cycles_total": int(skill.get("cycles_total", 0) or 0),
            "conclusive_cycles": int(skill.get("conclusive_cycles", 0) or 0),
            "current_difficulty": skill.get("current_difficulty"),
        }

    @classmethod
    def build(
        cls,
        *,
        learning_profile: dict[str, Any],
        archived_cycles_total: int,
        created_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProgressSnapshot:
        created_at = created_at or ProgressSnapshot.now_iso()
        skills = {
            str(skill_id): cls._normalize_skill(dict(skill_data or {}))
            for skill_id, skill_data in dict(
                learning_profile.get("skills") or {}
            ).items()
        }

        fingerprint_payload = {
            "created_at": created_at,
            "priority_skill_id": learning_profile.get(
                "current_priority_skill_id"
            ),
            "archived_cycles_total": int(archived_cycles_total),
            "skills": skills,
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                sort_keys=True,
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()[:16]

        return ProgressSnapshot(
            snapshot_id=f"progress_{fingerprint}",
            created_at=created_at,
            priority_skill_id=learning_profile.get(
                "current_priority_skill_id"
            ),
            skills=skills,
            archived_cycles_total=int(archived_cycles_total),
            metadata=dict(metadata or {}),
        )
