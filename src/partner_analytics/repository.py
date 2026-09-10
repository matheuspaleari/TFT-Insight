from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from src.persistence import get_database_url

from .models import ApiUsageEvent


class PartnerAnalyticsRepository:
    SCHEMA_VERSION = "2.0.0"

    def __init__(self, path=None) -> None:
        # "path" é aceito apenas por compatibilidade com chamadas antigas.
        # A persistência é sempre definida por DATABASE_URL.
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection]:
        connection = psycopg.connect(
            get_database_url(),
            row_factory=dict_row,
            autocommit=False,
        )
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS api_usage_events (
                        id BIGSERIAL PRIMARY KEY,
                        request_id TEXT NOT NULL,
                        partner_key TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        method TEXT NOT NULL,
                        status_code INTEGER NOT NULL,
                        latency_ms DOUBLE PRECISION NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        response_bytes BIGINT NOT NULL DEFAULT 0,
                        cache_hits INTEGER NOT NULL DEFAULT 0,
                        new_downloads INTEGER NOT NULL DEFAULT 0,
                        matches_analyzed INTEGER NOT NULL DEFAULT 0,
                        error_message TEXT
                    )
                    '''
                )

                cursor.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_usage_created_at
                    ON api_usage_events(created_at)
                    '''
                )
                cursor.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_usage_partner
                    ON api_usage_events(partner_key)
                    '''
                )
                cursor.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_usage_endpoint
                    ON api_usage_events(endpoint)
                    '''
                )

                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS analytics_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    '''
                )

                cursor.execute(
                    '''
                    INSERT INTO analytics_metadata(key, value)
                    VALUES ('schema_version', %s)
                    ON CONFLICT(key)
                    DO UPDATE SET value = EXCLUDED.value
                    ''',
                    (self.SCHEMA_VERSION,),
                )

    def record(self, event: ApiUsageEvent) -> None:
        self.initialize()

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
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
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    ''',
                    (
                        event.request_id,
                        event.partner_key,
                        event.endpoint,
                        event.method,
                        event.status_code,
                        event.latency_ms,
                        event.created_at,
                        event.response_bytes,
                        event.cache_hits,
                        event.new_downloads,
                        event.matches_analyzed,
                        event.error_message,
                    ),
                )

    def summary(self, *, hours: int = 24) -> dict:
        self.initialize()
        hours = max(1, int(hours))

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        COUNT(*) AS total_calls,
                        COUNT(*) FILTER (
                            WHERE status_code BETWEEN 200 AND 399
                        ) AS successful_calls,
                        AVG(latency_ms) AS average_latency_ms,
                        COALESCE(SUM(cache_hits), 0) AS cache_hits,
                        COALESCE(SUM(new_downloads), 0) AS new_downloads,
                        COALESCE(SUM(matches_analyzed), 0) AS matches_analyzed,
                        PERCENTILE_CONT(0.95)
                            WITHIN GROUP (ORDER BY latency_ms)
                            AS p95_latency_ms
                    FROM api_usage_events
                    WHERE created_at >= NOW() - make_interval(hours => %s)
                    ''',
                    (hours,),
                )
                row = cursor.fetchone()

        total = int(row["total_calls"] or 0)
        successful = int(row["successful_calls"] or 0)
        cache_hits = int(row["cache_hits"] or 0)
        new_downloads = int(row["new_downloads"] or 0)
        cache_total = cache_hits + new_downloads

        return {
            "total_calls": total,
            "successful_calls": successful,
            "success_rate": (
                successful / total * 100.0 if total else 0.0
            ),
            "average_latency_ms": float(
                row["average_latency_ms"] or 0.0
            ),
            "p95_latency_ms": float(
                row["p95_latency_ms"] or 0.0
            ),
            "cache_hits": cache_hits,
            "new_downloads": new_downloads,
            "cache_hit_rate": (
                cache_hits / cache_total * 100.0
                if cache_total else 0.0
            ),
            "matches_analyzed": int(
                row["matches_analyzed"] or 0
            ),
        }

    def recent_events(self, *, limit: int = 100) -> list[dict]:
        self.initialize()
        limit = max(1, min(int(limit), 1000))

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
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
                    LIMIT %s
                    ''',
                    (limit,),
                )
                rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def endpoint_usage(self, *, hours: int = 24) -> list[dict]:
        self.initialize()
        hours = max(1, int(hours))

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        endpoint,
                        COUNT(*) AS calls,
                        AVG(latency_ms) AS average_latency_ms,
                        COUNT(*) FILTER (
                            WHERE status_code >= 400
                        ) AS errors
                    FROM api_usage_events
                    WHERE created_at >= NOW() - make_interval(hours => %s)
                    GROUP BY endpoint
                    ORDER BY calls DESC
                    ''',
                    (hours,),
                )
                rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def daily_usage(self, *, days: int = 14) -> list[dict]:
        self.initialize()
        days = max(1, int(days))

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT
                        created_at::date AS day,
                        COUNT(*) AS calls,
                        AVG(latency_ms) AS average_latency_ms,
                        COUNT(*) FILTER (
                            WHERE status_code >= 400
                        ) AS errors
                    FROM api_usage_events
                    WHERE created_at >= NOW() - make_interval(days => %s)
                    GROUP BY created_at::date
                    ORDER BY day
                    ''',
                    (days,),
                )
                rows = cursor.fetchall()

        return [dict(row) for row in rows]
