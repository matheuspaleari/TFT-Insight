from __future__ import annotations

from threading import Lock

import psycopg
from psycopg.rows import dict_row

from src.persistence import get_database_url


_DB_LOCK = Lock()


def connect() -> psycopg.Connection:
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
        autocommit=False,
    )


def initialize_database() -> None:
    with _DB_LOCK:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGSERIAL PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        display_name TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'user'
                            CHECK(role IN ('admin', 'user')),
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        last_login_at TIMESTAMPTZ NULL
                    )
                    '''
                )

                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS auth_identities (
                        id BIGSERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL
                            REFERENCES users(id) ON DELETE CASCADE,
                        provider TEXT NOT NULL,
                        provider_id TEXT NULL,
                        password_hash TEXT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        UNIQUE(provider, provider_id),
                        UNIQUE(user_id, provider)
                    )
                    '''
                )

                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS login_events (
                        id BIGSERIAL PRIMARY KEY,
                        user_id BIGINT NULL
                            REFERENCES users(id) ON DELETE SET NULL,
                        email TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        provider TEXT NOT NULL,
                        occurred_at TIMESTAMPTZ NOT NULL,
                        reason TEXT NULL
                    )
                    '''
                )

                cursor.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_login_events_user_id
                    ON login_events(user_id)
                    '''
                )

                cursor.execute(
                    '''
                    CREATE INDEX IF NOT EXISTS idx_login_events_occurred_at
                    ON login_events(occurred_at)
                    '''
                )

                cursor.execute(
                    '''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
                    ON users (LOWER(email))
                    '''
                )

            db.commit()
