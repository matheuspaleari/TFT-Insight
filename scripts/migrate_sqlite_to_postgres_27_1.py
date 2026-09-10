from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integration_engine.auth.database import initialize_database as init_auth
from src.partner_analytics import PartnerAnalyticsRepository
from src.persistence import get_database_url


def _parse_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _sqlite_rows(path: Path, table: str) -> list[dict]:
    if not path.exists():
        return []
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in db.execute(f"SELECT * FROM {table}")]
    finally:
        db.close()


def migrate_auth(source: Path, *, dry_run: bool) -> dict:
    users = _sqlite_rows(source, "users")
    identities = _sqlite_rows(source, "auth_identities")
    events = _sqlite_rows(source, "login_events")

    if dry_run:
        return {
            "users": len(users),
            "auth_identities": len(identities),
            "login_events": len(events),
        }

    init_auth()

    with psycopg.connect(get_database_url(), row_factory=dict_row) as pg:
        with pg.cursor() as cur:
            for row in users:
                cur.execute(
                    """
                    INSERT INTO users (
                        id, email, display_name, role, is_active,
                        created_at, updated_at, last_login_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        row["id"],
                        row["email"],
                        row["display_name"],
                        row["role"],
                        bool(row["is_active"]),
                        _parse_dt(row["created_at"]),
                        _parse_dt(row["updated_at"]),
                        _parse_dt(row["last_login_at"]),
                    ),
                )

            for row in identities:
                cur.execute(
                    """
                    INSERT INTO auth_identities (
                        id, user_id, provider, provider_id,
                        password_hash, created_at, updated_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        row["id"],
                        row["user_id"],
                        row["provider"],
                        row["provider_id"],
                        row["password_hash"],
                        _parse_dt(row["created_at"]),
                        _parse_dt(row["updated_at"]),
                    ),
                )

            for row in events:
                cur.execute(
                    """
                    INSERT INTO login_events (
                        id, user_id, email, success, provider,
                        occurred_at, reason
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        row["id"],
                        row["user_id"],
                        row["email"],
                        bool(row["success"]),
                        row["provider"],
                        _parse_dt(row["occurred_at"]),
                        row["reason"],
                    ),
                )

            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('users', 'id'),
                    GREATEST(COALESCE((SELECT MAX(id) FROM users), 1), 1),
                    true
                )
                """
            )
            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('auth_identities', 'id'),
                    GREATEST(COALESCE((SELECT MAX(id) FROM auth_identities), 1), 1),
                    true
                )
                """
            )
            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('login_events', 'id'),
                    GREATEST(COALESCE((SELECT MAX(id) FROM login_events), 1), 1),
                    true
                )
                """
            )

        pg.commit()

    return {
        "users": len(users),
        "auth_identities": len(identities),
        "login_events": len(events),
    }


def migrate_analytics(source: Path, *, dry_run: bool) -> dict:
    events = _sqlite_rows(source, "api_usage_events")
    metadata = _sqlite_rows(source, "analytics_metadata")

    if dry_run:
        return {
            "api_usage_events": len(events),
            "analytics_metadata": len(metadata),
        }

    PartnerAnalyticsRepository().initialize()

    with psycopg.connect(get_database_url(), row_factory=dict_row) as pg:
        with pg.cursor() as cur:
            for row in events:
                cur.execute(
                    """
                    INSERT INTO api_usage_events (
                        id, request_id, partner_key, endpoint, method,
                        status_code, latency_ms, created_at, response_bytes,
                        cache_hits, new_downloads, matches_analyzed, error_message
                    )
                    VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        row["id"],
                        row["request_id"],
                        row["partner_key"],
                        row["endpoint"],
                        row["method"],
                        row["status_code"],
                        row["latency_ms"],
                        _parse_dt(row["created_at"]),
                        row["response_bytes"],
                        row["cache_hits"],
                        row["new_downloads"],
                        row["matches_analyzed"],
                        row["error_message"],
                    ),
                )

            for row in metadata:
                cur.execute(
                    """
                    INSERT INTO analytics_metadata(key, value)
                    VALUES (%s, %s)
                    ON CONFLICT(key)
                    DO UPDATE SET value = EXCLUDED.value
                    """,
                    (row["key"], row["value"]),
                )

            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence('api_usage_events', 'id'),
                    GREATEST(
                        COALESCE((SELECT MAX(id) FROM api_usage_events), 1),
                        1
                    ),
                    true
                )
                """
            )

        pg.commit()

    return {
        "api_usage_events": len(events),
        "analytics_metadata": len(metadata),
    }


def postgres_counts() -> dict:
    tables = (
        "users",
        "auth_identities",
        "login_events",
        "api_usage_events",
    )
    result = {}
    with psycopg.connect(get_database_url(), row_factory=dict_row) as pg:
        with pg.cursor() as cur:
            for table in tables:
                cur.execute(f"SELECT COUNT(*) AS total FROM {table}")
                result[table] = int(cur.fetchone()["total"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migra autenticação e analytics SQLite para PostgreSQL."
    )
    parser.add_argument(
        "--auth-source",
        default=str(ROOT / "database" / "tft_insight_auth.db"),
    )
    parser.add_argument(
        "--analytics-source",
        default=str(ROOT / "data" / "partner" / "partner_analytics.db"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas conta registros; não grava no PostgreSQL.",
    )
    args = parser.parse_args()

    auth_source = Path(args.auth_source)
    analytics_source = Path(args.analytics_source)

    print("=" * 100)
    print("ROADMAP 27.1 - MIGRAÇÃO SQLITE -> POSTGRESQL")
    print("=" * 100)
    print(f"Auth source      : {auth_source}")
    print(f"Analytics source : {analytics_source}")
    print(f"Dry run          : {args.dry_run}")

    auth = migrate_auth(auth_source, dry_run=args.dry_run)
    analytics = migrate_analytics(analytics_source, dry_run=args.dry_run)

    print("-" * 100)
    print("SQLite encontrado:")
    for key, value in {**auth, **analytics}.items():
        print(f"  {key:22} {value}")

    if not args.dry_run:
        counts = postgres_counts()
        print("-" * 100)
        print("PostgreSQL depois da migração:")
        for key, value in counts.items():
            print(f"  {key:22} {value}")

        expected = {
            "users": auth["users"],
            "auth_identities": auth["auth_identities"],
            "login_events": auth["login_events"],
            "api_usage_events": analytics["api_usage_events"],
        }

        failures = [
            table
            for table, count in expected.items()
            if counts.get(table, 0) < count
        ]

        if failures:
            print("RESULTADO: REVISAR")
            print("Contagens menores que o SQLite:", ", ".join(failures))
            return 1

        print("RESULTADO: MIGRAÇÃO CONCLUÍDA SEM PERDA POR CONTAGEM")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
