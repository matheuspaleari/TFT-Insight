from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from .models import ApiUsageEvent


class PartnerAnalyticsRepository:
    SCHEMA_VERSION = "1.1.0"

    def __init__(
        self,
        path: str | Path = "data/partner/partner_analytics.db",
    ) -> None:
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(
            self.path,
            timeout=30.0,
        )
        connection.row_factory = sqlite3.Row

        try:
            connection.execute("PRAGMA journal_mode=WAL;")
            connection.execute("PRAGMA synchronous=NORMAL;")
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS api_usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    partner_key TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    response_bytes INTEGER NOT NULL DEFAULT 0,
                    cache_hits INTEGER NOT NULL DEFAULT 0,
                    new_downloads INTEGER NOT NULL DEFAULT 0,
                    matches_analyzed INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_usage_created_at
                ON api_usage_events(created_at);

                CREATE INDEX IF NOT EXISTS idx_usage_partner
                ON api_usage_events(partner_key);

                CREATE INDEX IF NOT EXISTS idx_usage_endpoint
                ON api_usage_events(endpoint);

                CREATE TABLE IF NOT EXISTS analytics_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

            connection.execute(
                """
                INSERT INTO analytics_metadata(key, value)
                VALUES ('schema_version', ?)
                ON CONFLICT(key)
                DO UPDATE SET value = excluded.value
                """,
                (self.SCHEMA_VERSION,),
            )

    def record(self, event: ApiUsageEvent) -> None:
        self.initialize()

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO api_usage_events (
                    request_id,
                    partner_key,
                    endpoint,
                    method,
                    status_code,
                    latency_ms,
                    created_at,
                    response_bytes,
                    cache_hits,
                    new_downloads,
                    matches_analyzed,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.request_id,
                    event.partner_key,
                    event.endpoint,
                    event.method,
                    event.status_code,
                    event.latency_ms,
                    event.created_at.isoformat(),
                    event.response_bytes,
                    event.cache_hits,
                    event.new_downloads,
                    event.matches_analyzed,
                    event.error_message,
                ),
            )

    def summary(self, *, hours: int = 24) -> dict:
        self.initialize()

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_calls,
                    SUM(
                        CASE WHEN status_code BETWEEN 200 AND 399
                        THEN 1 ELSE 0 END
                    ) AS successful_calls,
                    AVG(latency_ms) AS average_latency_ms,
                    SUM(cache_hits) AS cache_hits,
                    SUM(new_downloads) AS new_downloads,
                    SUM(matches_analyzed) AS matches_analyzed
                FROM api_usage_events
                WHERE datetime(created_at) >= datetime('now', ?)
                """,
                (f"-{hours} hours",),
            ).fetchone()

            latencies = [
                float(row["latency_ms"])
                for row in connection.execute(
                    """
                    SELECT latency_ms
                    FROM api_usage_events
                    WHERE datetime(created_at) >= datetime('now', ?)
                    ORDER BY latency_ms
                    """,
                    (f"-{hours} hours",),
                ).fetchall()
            ]

        total = int(row["total_calls"] or 0)
        successful = int(row["successful_calls"] or 0)
        cache_hits = int(row["cache_hits"] or 0)
        new_downloads = int(row["new_downloads"] or 0)

        p95 = 0.0

        if latencies:
            index = min(
                len(latencies) - 1,
                max(0, int(len(latencies) * 0.95) - 1),
            )
            p95 = latencies[index]

        cache_total = cache_hits + new_downloads

        return {
            "total_calls": total,
            "successful_calls": successful,
            "success_rate": (
                successful / total * 100.0
                if total
                else 0.0
            ),
            "average_latency_ms": float(
                row["average_latency_ms"] or 0.0
            ),
            "p95_latency_ms": p95,
            "cache_hits": cache_hits,
            "new_downloads": new_downloads,
            "cache_hit_rate": (
                cache_hits / cache_total * 100.0
                if cache_total
                else 0.0
            ),
            "matches_analyzed": int(
                row["matches_analyzed"] or 0
            ),
        }

    def recent_events(
        self,
        *,
        limit: int = 100,
    ) -> list[dict]:
        self.initialize()

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    request_id,
                    partner_key,
                    endpoint,
                    method,
                    status_code,
                    latency_ms,
                    created_at,
                    response_bytes,
                    cache_hits,
                    new_downloads,
                    matches_analyzed,
                    error_message
                FROM api_usage_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def endpoint_usage(
        self,
        *,
        hours: int = 24,
    ) -> list[dict]:
        self.initialize()

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    endpoint,
                    COUNT(*) AS calls,
                    AVG(latency_ms) AS average_latency_ms,
                    SUM(
                        CASE WHEN status_code >= 400
                        THEN 1 ELSE 0 END
                    ) AS errors
                FROM api_usage_events
                WHERE datetime(created_at) >= datetime('now', ?)
                GROUP BY endpoint
                ORDER BY calls DESC
                """,
                (f"-{hours} hours",),
            ).fetchall()

        return [dict(row) for row in rows]

    def daily_usage(
        self,
        *,
        days: int = 14,
    ) -> list[dict]:
        self.initialize()

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    date(created_at) AS day,
                    COUNT(*) AS calls,
                    AVG(latency_ms) AS average_latency_ms,
                    SUM(
                        CASE WHEN status_code >= 400
                        THEN 1 ELSE 0 END
                    ) AS errors
                FROM api_usage_events
                WHERE datetime(created_at) >= datetime('now', ?)
                GROUP BY date(created_at)
                ORDER BY day
                """,
                (f"-{days} days",),
            ).fetchall()

        return [dict(row) for row in rows]
