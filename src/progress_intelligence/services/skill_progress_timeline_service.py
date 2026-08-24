from __future__ import annotations

from collections import defaultdict

from ..models.skill_progress_point import SkillProgressPoint
from ..models.progress_snapshot import ProgressSnapshot


class SkillProgressTimelineService:
    @classmethod
    def build(
        cls,
        *,
        snapshots: list[ProgressSnapshot],
    ) -> dict[str, list[SkillProgressPoint]]:
        timelines: dict[str, list[SkillProgressPoint]] = defaultdict(list)

        for snapshot in snapshots:
            for skill_id, skill in snapshot.skills.items():
                score = skill.get("score")
                timelines[skill_id].append(
                    SkillProgressPoint(
                        snapshot_id=snapshot.snapshot_id,
                        created_at=snapshot.created_at,
                        skill_id=skill_id,
                        score=None if score is None else float(score),
                        level=str(skill.get("level", "NOT_EVALUATED")),
                        trend=str(
                            skill.get(
                                "trend",
                                "INSUFFICIENT_HISTORY",
                            )
                        ),
                        trend_confidence=str(
                            skill.get(
                                "trend_confidence",
                                "LOW",
                            )
                        ),
                        cycles_total=int(
                            skill.get(
                                "cycles_total",
                                0,
                            )
                            or 0
                        ),
                        conclusive_cycles=int(
                            skill.get(
                                "conclusive_cycles",
                                0,
                            )
                            or 0
                        ),
                        difficulty=skill.get(
                            "current_difficulty"
                        ),
                    )
                )

        return dict(timelines)
