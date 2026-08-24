from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.partner_analytics import PartnerAnalyticsRepository


class DashboardAnalyticsService:
    def __init__(self) -> None:
        self.repository = PartnerAnalyticsRepository(
            PROJECT_ROOT
            / "data"
            / "partner"
            / "partner_analytics.db"
        )
        self.repository.initialize()

    def summary(self, *, hours: int = 24) -> dict:
        return self.repository.summary(hours=hours)

    def daily_usage(self, *, days: int = 14) -> list[dict]:
        return self.repository.daily_usage(days=days)

    def recent_events(self, *, limit: int = 100) -> list[dict]:
        return self.repository.recent_events(limit=limit)
