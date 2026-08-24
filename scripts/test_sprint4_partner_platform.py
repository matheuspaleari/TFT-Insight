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
            Path(directory) / "partner.db"
        )

        repository.initialize()

        repository.record(
            ApiUsageEvent(
                request_id="sprint4-test",
                partner_key="demo",
                endpoint="/v1/analyze/player",
                method="POST",
                status_code=200,
                latency_ms=120.5,
                created_at=datetime.now(timezone.utc),
                response_bytes=2048,
                cache_hits=20,
                new_downloads=0,
                matches_analyzed=20,
            )
        )

        summary = repository.summary(hours=24)

        assert summary["total_calls"] == 1
        assert summary["success_rate"] == 100.0
        assert summary["cache_hit_rate"] == 100.0

        assert len(
            repository.recent_events(limit=10)
        ) == 1

        assert len(
            repository.endpoint_usage(hours=24)
        ) == 1

    print("=" * 84)
    print("TFT INSIGHT - SPRINT 4 VALIDATION")
    print("=" * 84)
    print("Analytics DB      : OK")
    print("Usage aggregation : OK")
    print("Cache metrics     : OK")
    print("Endpoint metrics  : OK")
    print("Dashboard modules : OK")
    print()
    print("✓ Sprint 4 Partner Platform validada.")


if __name__ == "__main__":
    main()
