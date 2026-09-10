from __future__ import annotations

from datetime import datetime, timezone

from src.integration_engine.auth.database import connect, initialize_database
from src.integration_engine.auth.models import UserRecord


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _row_to_user(row) -> UserRecord | None:
    if row is None:
        return None

    return UserRecord(
        id=int(row["id"]),
        email=str(row["email"]),
        display_name=str(row["display_name"]),
        role=str(row["role"]),
        is_active=bool(row["is_active"]),
        created_at=_as_iso(row["created_at"]) or "",
        updated_at=_as_iso(row["updated_at"]) or "",
        last_login_at=_as_iso(row["last_login_at"]),
    )


class UserRepository:
    def __init__(self) -> None:
        initialize_database()

    def get_by_email(self, email: str) -> UserRecord | None:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT *
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    ''',
                    (email.strip(),),
                )
                row = cursor.fetchone()
        return _row_to_user(row)

    def get_by_id(self, user_id: int) -> UserRecord | None:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE id = %s",
                    (user_id,),
                )
                row = cursor.fetchone()
        return _row_to_user(row)

    def create_password_user(
        self,
        *,
        email: str,
        display_name: str,
        password_hash: str,
        role: str,
    ) -> UserRecord:
        now = _now()
        normalized_email = email.strip().lower()

        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO users (
                        email, display_name, role, is_active,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, TRUE, %s, %s)
                    RETURNING id
                    ''',
                    (
                        normalized_email,
                        display_name.strip(),
                        role,
                        now,
                        now,
                    ),
                )
                user_id = int(cursor.fetchone()["id"])

                cursor.execute(
                    '''
                    INSERT INTO auth_identities (
                        user_id, provider, provider_id,
                        password_hash, created_at, updated_at
                    )
                    VALUES (%s, 'password', NULL, %s, %s, %s)
                    ''',
                    (user_id, password_hash, now, now),
                )

            db.commit()

        user = self.get_by_id(user_id)
        if user is None:
            raise RuntimeError("Falha ao recuperar usuário recém-criado.")
        return user

    def get_password_hash(self, user_id: int) -> str | None:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT password_hash
                    FROM auth_identities
                    WHERE user_id = %s AND provider = 'password'
                    ''',
                    (user_id,),
                )
                row = cursor.fetchone()

        if row is None or row["password_hash"] is None:
            return None
        return str(row["password_hash"])

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        now = _now()
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    UPDATE auth_identities
                    SET password_hash = %s, updated_at = %s
                    WHERE user_id = %s AND provider = 'password'
                    ''',
                    (password_hash, now, user_id),
                )
            db.commit()

    def mark_login(self, user_id: int) -> None:
        now = _now()
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    UPDATE users
                    SET last_login_at = %s, updated_at = %s
                    WHERE id = %s
                    ''',
                    (now, now, user_id),
                )
            db.commit()

    def add_login_event(
        self,
        *,
        user_id: int | None,
        email: str,
        success: bool,
        provider: str = "password",
        reason: str | None = None,
    ) -> None:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO login_events (
                        user_id, email, success, provider,
                        occurred_at, reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        user_id,
                        email.strip().lower(),
                        success,
                        provider,
                        _now(),
                        reason,
                    ),
                )
            db.commit()

    def count_login_events(self) -> int:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS total FROM login_events")
                row = cursor.fetchone()
        return int(row["total"])
