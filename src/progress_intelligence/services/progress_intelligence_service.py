from __future__ import annotations

from .overall_player_development_service import (
    OverallPlayerDevelopmentService,
)
from .progress_insight_service import ProgressInsightService
from .skill_progress_timeline_service import (
    SkillProgressTimelineService,
)


class ProgressIntelligenceService:
    @classmethod
    def build(
        cls,
        *,
        snapshots,
        primary_skill_id: str | None,
    ) -> dict:
        timelines = SkillProgressTimelineService.build(
            snapshots=snapshots
        )

        development = (
            OverallPlayerDevelopmentService.summarize(
                timelines=timelines,
                primary_skill_id=primary_skill_id,
            )
        )

        insights = ProgressInsightService.build(
            timelines=timelines,
            development_summary=development,
        )

        return {
            "timelines": {
                skill_id: [
                    point.to_dict()
                    for point in points
                ]
                for skill_id, points in timelines.items()
            },
            "overall_development": development.to_dict(),
            "insights": [
                item.to_dict()
                for item in insights
            ],
        }
