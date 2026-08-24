from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.partner_analytics.models import ApiUsageEvent
from src.partner_analytics.repository import (
    PartnerAnalyticsRepository,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = PartnerAnalyticsRepository(
            Path(directory) / "analytics.db"
        )
        repository.initialize()

        repository.record(
            ApiUsageEvent(
                request_id="test-1",
                partner_key="development",
                endpoint="/v1/analyze/player",
                method="POST",
                status_code=200,
                latency_ms=123.4,
                created_at=datetime.now(timezone.utc),
                response_bytes=1500,
                cache_hits=20,
                new_downloads=0,
                matches_analyzed=20,
            )
        )

        summary = repository.summary(hours=24)
        events = repository.recent_events(limit=10)
        endpoints = repository.endpoint_usage(hours=24)

        assert summary["total_calls"] == 1
        assert summary["success_rate"] == 100.0
        assert summary["cache_hit_rate"] == 100.0
        assert len(events) == 1
        assert len(endpoints) == 1

    print("=" * 80)
    print("TFT INSIGHT - PARTNER DASHBOARD VALIDATION")
    print("=" * 80)
    print("SQLite analytics : OK")
    print("Usage summary    : OK")
    print("Recent events    : OK")
    print("Endpoint metrics : OK")
    print()
    print("✓ Partner Dashboard backend validado.")


if __name__ == "__main__":
    main()
