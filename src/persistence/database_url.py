from __future__ import annotations

import os


class DatabaseConfigurationError(RuntimeError):
    pass


def get_database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise DatabaseConfigurationError(
            "DATABASE_URL não configurada. "
            "Configure a conexão PostgreSQL antes de iniciar o TFT Insight."
        )

    # Alguns provedores ainda entregam postgres://.
    # psycopg aceita postgresql://, então normalizamos de forma explícita.
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://"):]

    if not value.startswith(("postgresql://", "postgresql+psycopg://")):
        raise DatabaseConfigurationError(
            "DATABASE_URL precisa apontar para PostgreSQL."
        )

    if value.startswith("postgresql+psycopg://"):
        value = "postgresql://" + value[len("postgresql+psycopg://"):]

    return value
