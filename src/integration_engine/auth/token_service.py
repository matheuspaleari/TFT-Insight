from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt


class TokenConfigurationError(RuntimeError):
    pass


class TokenService:
    def __init__(self) -> None:
        self._algorithm = "HS256"

    @staticmethod
    def _secret() -> str:
        secret = os.getenv("TFT_INSIGHT_AUTH_SECRET", "").strip()
        if len(secret) < 32:
            raise TokenConfigurationError(
                "TFT_INSIGHT_AUTH_SECRET precisa ter pelo menos 32 caracteres."
            )
        return secret

    @staticmethod
    def _ttl_minutes() -> int:
        raw = os.getenv("TFT_INSIGHT_AUTH_TOKEN_MINUTES", "720").strip()
        try:
            ttl = int(raw)
        except ValueError:
            ttl = 720
        return max(15, min(ttl, 10080))

    def create_access_token(self, *, user_id: int, email: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=self._ttl_minutes()),
            "type": "access",
        }
        return jwt.encode(payload, self._secret(), algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict:
        payload = jwt.decode(
            token,
            self._secret(),
            algorithms=[self._algorithm],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Tipo de token inválido.")
        return payload
