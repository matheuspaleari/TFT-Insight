from __future__ import annotations

import os
import re
from functools import lru_cache

import jwt
from psycopg.errors import UniqueViolation

from src.integration_engine.auth.models import UserRecord
from src.integration_engine.auth.password_service import PasswordService
from src.integration_engine.auth.token_service import TokenService
from src.integration_engine.auth.user_repository import UserRepository


_EMAIL_RE = re.compile(
    r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}$",
    re.IGNORECASE,
)


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(
        self,
        repository: UserRepository | None = None,
        passwords: PasswordService | None = None,
        tokens: TokenService | None = None,
    ) -> None:
        self.repository = repository or UserRepository()
        self.passwords = passwords or PasswordService()
        self.tokens = tokens or TokenService()

    @staticmethod
    def _normalize_email(email: str) -> str:
        normalized = email.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise AuthError("Informe um e-mail válido.")
        return normalized

    @staticmethod
    def _validate_display_name(display_name: str) -> str:
        value = " ".join(display_name.strip().split())
        if len(value) < 2:
            raise AuthError("Informe seu nome.")
        if len(value) > 80:
            raise AuthError("Nome muito longo.")
        return value

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise AuthError("A senha precisa ter pelo menos 8 caracteres.")
        if len(password) > 128:
            raise AuthError("Senha muito longa.")
        if not any(ch.isalpha() for ch in password):
            raise AuthError("A senha precisa conter pelo menos uma letra.")
        if not any(ch.isdigit() for ch in password):
            raise AuthError("A senha precisa conter pelo menos um número.")

    @staticmethod
    def _initial_role(email: str) -> str:
        admin_email = os.getenv("TFT_INSIGHT_ADMIN_EMAIL", "").strip().lower()
        return "admin" if admin_email and email == admin_email else "user"

    def register(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
    ) -> tuple[UserRecord, str]:
        normalized_email = self._normalize_email(email)
        clean_name = self._validate_display_name(display_name)
        self._validate_password(password)

        if self.repository.get_by_email(normalized_email) is not None:
            raise AuthError("Já existe uma conta com este e-mail.")

        password_hash = self.passwords.hash(password)

        try:
            user = self.repository.create_password_user(
                email=normalized_email,
                display_name=clean_name,
                password_hash=password_hash,
                role=self._initial_role(normalized_email),
            )
        except UniqueViolation as exc:
            raise AuthError("Já existe uma conta com este e-mail.") from exc

        self.repository.add_login_event(
            user_id=user.id,
            email=user.email,
            success=True,
            provider="password",
            reason="registration",
        )
        self.repository.mark_login(user.id)

        refreshed = self.repository.get_by_id(user.id) or user
        token = self.tokens.create_access_token(
            user_id=refreshed.id,
            email=refreshed.email,
            role=refreshed.role,
        )
        return refreshed, token

    def login(self, *, email: str, password: str) -> tuple[UserRecord, str]:
        try:
            normalized_email = self._normalize_email(email)
        except AuthError:
            normalized_email = email.strip().lower()
            self.repository.add_login_event(
                user_id=None,
                email=normalized_email,
                success=False,
                reason="invalid_credentials",
            )
            raise AuthError("E-mail ou senha inválidos.")

        user = self.repository.get_by_email(normalized_email)
        if user is None:
            self.repository.add_login_event(
                user_id=None,
                email=normalized_email,
                success=False,
                reason="invalid_credentials",
            )
            raise AuthError("E-mail ou senha inválidos.")

        if not user.is_active:
            self.repository.add_login_event(
                user_id=user.id,
                email=user.email,
                success=False,
                reason="inactive_user",
            )
            raise AuthError("Esta conta está desativada.")

        password_hash = self.repository.get_password_hash(user.id)
        if not password_hash or not self.passwords.verify(password, password_hash):
            self.repository.add_login_event(
                user_id=user.id,
                email=user.email,
                success=False,
                reason="invalid_credentials",
            )
            raise AuthError("E-mail ou senha inválidos.")

        if self.passwords.needs_rehash(password_hash):
            self.repository.update_password_hash(
                user.id,
                self.passwords.hash(password),
            )

        self.repository.mark_login(user.id)
        self.repository.add_login_event(
            user_id=user.id,
            email=user.email,
            success=True,
        )

        refreshed = self.repository.get_by_id(user.id) or user
        token = self.tokens.create_access_token(
            user_id=refreshed.id,
            email=refreshed.email,
            role=refreshed.role,
        )
        return refreshed, token

    def user_from_token(self, token: str) -> UserRecord:
        try:
            payload = self.tokens.decode_access_token(token)
            user_id = int(payload["sub"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
            raise AuthError("Sessão inválida ou expirada.") from exc

        user = self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthError("Sessão inválida ou conta desativada.")

        return user

    def require_admin(self, token: str) -> UserRecord:
        user = self.user_from_token(token)
        if user.role != "admin":
            raise AuthError("Acesso restrito a administradores.")
        return user

    def list_users_for_admin(self, token: str) -> list[UserRecord]:
        self.require_admin(token)
        return self.repository.list_users()


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    return AuthService()
