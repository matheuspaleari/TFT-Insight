from fastapi import (
    Header,
    HTTPException,
    status,
)

from src.integration_engine.config import (
    IntegrationSettings,
)


_SETTINGS = IntegrationSettings.from_environment()


def require_api_key(
    x_api_key: str | None = Header(
        default=None,
        alias="X-API-Key",
    ),
) -> str:
    if (
        _SETTINGS.environment == "development"
        and _SETTINGS.allow_unauthenticated_dev
        and not _SETTINGS.api_keys
    ):
        return "development"

    if (
        x_api_key is None
        or x_api_key not in _SETTINGS.api_keys
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida ou ausente.",
        )

    return x_api_key
