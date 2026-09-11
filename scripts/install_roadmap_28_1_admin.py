from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = ROOT / "scripts" / "archive" / f"roadmap_28_1_backup_{STAMP}"

FILES = {}


FILES["src/integration_engine/auth/user_repository.py"] = r'''from __future__ import annotations

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
                    """
                    SELECT *
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    """,
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

    def list_users(self) -> list[UserRecord]:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM users
                    ORDER BY created_at DESC, id DESC
                    """
                )
                rows = cursor.fetchall()

        return [
            user
            for row in rows
            if (user := _row_to_user(row)) is not None
        ]

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
                    """
                    INSERT INTO users (
                        email, display_name, role, is_active,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, TRUE, %s, %s)
                    RETURNING id
                    """,
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
                    """
                    INSERT INTO auth_identities (
                        user_id, provider, provider_id,
                        password_hash, created_at, updated_at
                    )
                    VALUES (%s, 'password', NULL, %s, %s, %s)
                    """,
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
                    """
                    SELECT password_hash
                    FROM auth_identities
                    WHERE user_id = %s AND provider = 'password'
                    """,
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
                    """
                    UPDATE auth_identities
                    SET password_hash = %s, updated_at = %s
                    WHERE user_id = %s AND provider = 'password'
                    """,
                    (password_hash, now, user_id),
                )
            db.commit()

    def mark_login(self, user_id: int) -> None:
        now = _now()
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE users
                    SET last_login_at = %s, updated_at = %s
                    WHERE id = %s
                    """,
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
                    """
                    INSERT INTO login_events (
                        user_id, email, success, provider,
                        occurred_at, reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
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
'''


FILES["src/integration_engine/auth/service.py"] = r'''from __future__ import annotations

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
'''


FILES["src/integration_engine/api/routes/auth.py"] = r'''from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from src.integration_engine.auth.service import AuthError, get_auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer inválido.",
        )

    return token.strip()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest) -> AuthResponse:
    service = get_auth_service()

    try:
        user, token = service.register(
            email=payload.email,
            display_name=payload.display_name,
            password=payload.password,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return AuthResponse(
        access_token=token,
        user=user.public_dict(),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    service = get_auth_service()

    try:
        user, token = service.login(
            email=payload.email,
            password=payload.password,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return AuthResponse(
        access_token=token,
        user=user.public_dict(),
    )


@router.get("/me")
def me(token: Annotated[str, Depends(_bearer_token)]) -> dict:
    service = get_auth_service()

    try:
        user = service.user_from_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return {"user": user.public_dict()}


@router.get("/admin/users")
def admin_users(
    token: Annotated[str, Depends(_bearer_token)],
) -> dict:
    service = get_auth_service()

    try:
        users = service.list_users_for_admin(token)
    except AuthError as exc:
        message = str(exc)
        code = (
            status.HTTP_403_FORBIDDEN
            if "administradores" in message
            else status.HTTP_401_UNAUTHORIZED
        )
        raise HTTPException(
            status_code=code,
            detail=message,
        ) from exc

    return {
        "users": [user.public_dict() for user in users],
        "total": len(users),
    }
'''


FILES["partner_platform/auth/api_client.py"] = r'''from __future__ import annotations

import os

import requests


class AuthApiError(RuntimeError):
    pass


def _api_base_url() -> str:
    return os.getenv(
        "TFT_INSIGHT_API_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")


def _request(method: str, path: str, **kwargs) -> dict:
    try:
        response = requests.request(
            method,
            f"{_api_base_url()}{path}",
            timeout=15,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise AuthApiError(
            "Não foi possível conectar à API do TFT Insight."
        ) from exc

    try:
        body = response.json()
    except ValueError:
        body = {}

    if not response.ok:
        detail = body.get("detail") if isinstance(body, dict) else None
        raise AuthApiError(
            str(detail or "Não foi possível concluir a autenticação.")
        )

    if not isinstance(body, dict):
        raise AuthApiError("Resposta de autenticação inválida.")

    return body


def register(
    *,
    email: str,
    display_name: str,
    password: str,
) -> dict:
    return _request(
        "POST",
        "/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "password": password,
        },
    )


def login(*, email: str, password: str) -> dict:
    return _request(
        "POST",
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def me(token: str) -> dict:
    return _request(
        "GET",
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )


def admin_users(token: str) -> dict:
    return _request(
        "GET",
        "/auth/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
'''


FILES["partner_platform/pages/admin_page.py"] = r'''from __future__ import annotations

from datetime import datetime

import streamlit as st

from partner_platform.auth import api_client
from partner_platform.auth.session import current_user


def _format_date(value: str | None) -> str:
    if not value:
        return "Nunca"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value)


def render(*, context) -> None:
    user = current_user() or {}

    if user.get("role") != "admin":
        st.error("Acesso restrito a administradores.")
        return

    st.title("Administração")
    st.caption("Gerenciamento e visão geral dos usuários do TFT Insight.")

    token = str(st.session_state.get("tft_auth_token", "")).strip()
    if not token:
        st.error("Sessão de autenticação não encontrada.")
        return

    try:
        payload = api_client.admin_users(token)
    except api_client.AuthApiError as exc:
        st.error(str(exc))
        return

    users = payload.get("users", [])
    if not isinstance(users, list):
        users = []

    total = len(users)
    active = sum(bool(item.get("is_active")) for item in users)
    admins = sum(item.get("role") == "admin" for item in users)

    columns = st.columns(4)
    columns[0].metric("Usuários", total)
    columns[1].metric("Ativos", active)
    columns[2].metric("Inativos", total - active)
    columns[3].metric("Administradores", admins)

    st.markdown("### Usuários cadastrados")

    if not users:
        st.info("Nenhum usuário cadastrado.")
        return

    rows = []
    for item in users:
        rows.append(
            {
                "Nome": item.get("display_name", ""),
                "E-mail": item.get("email", ""),
                "Role": item.get("role", "user"),
                "Status": "Ativo" if item.get("is_active") else "Inativo",
                "Criado em": _format_date(item.get("created_at")),
                "Último login": _format_date(item.get("last_login_at")),
            }
        )

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )
'''


FILES["partner_platform/navigation/catalog.py"] = r'''from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NavigationItem:
    page: str
    label: str
    icon: str
    group: str
    admin_only: bool = False

    @property
    def display_label(self) -> str:
        return f"{self.icon} {self.label}"


class NavigationCatalog:
    """Navegação pública enxuta do TFT Insight."""

    def __init__(
        self,
        items: tuple[NavigationItem, ...],
    ) -> None:
        self.items = items

    @classmethod
    def default(cls) -> "NavigationCatalog":
        return cls(
            (
                NavigationItem(
                    page="Home",
                    label="Início",
                    icon="⌂",
                    group="Principal",
                ),
                NavigationItem(
                    page="Benchmark",
                    label="Análise",
                    icon="◆",
                    group="Principal",
                ),
                NavigationItem(
                    page="Settings",
                    label="Configurações",
                    icon="⚙",
                    group="Principal",
                ),
                NavigationItem(
                    page="Admin",
                    label="Admin",
                    icon="▣",
                    group="Principal",
                    admin_only=True,
                ),
            )
        )

    def visible_items(
        self,
        group: str,
        *,
        is_admin: bool = False,
    ) -> tuple[NavigationItem, ...]:
        return tuple(
            item
            for item in self.items
            if item.group == group
            and (not item.admin_only or is_admin)
        )

    def labels_for(
        self,
        group: str,
        *,
        is_admin: bool = False,
    ) -> tuple[str, ...]:
        return tuple(
            item.display_label
            for item in self.visible_items(
                group,
                is_admin=is_admin,
            )
        )

    def page_from_label(
        self,
        label: str | None,
    ) -> str:
        for item in self.items:
            if item.display_label == label:
                return item.page

        return "Home"
'''


FILES["partner_platform/platform_core/context.py"] = r'''from dataclasses import dataclass
import os

import streamlit as st

from partner_platform.auth.session import current_user
from partner_platform.components import (
    current_session_panel,
    sidebar_brand,
)
from partner_platform.navigation import NavigationCatalog


@dataclass(slots=True, frozen=True)
class PlatformContext:
    page: str
    api_base_url: str
    api_key: str | None
    environment: str = "Development"
    platform_version: str = "v0.6.0-alpha.2"

    @classmethod
    def from_sidebar(cls):
        sidebar_brand()
        current_session_panel()

        catalog = NavigationCatalog.default()

        user = current_user() or {}
        is_admin = user.get("role") == "admin"

        pending_page = st.session_state.pop(
            "_tft_navigation_target",
            None,
        )

        if pending_page:
            pending_label = next(
                (
                    item.display_label
                    for item in catalog.visible_items(
                        "Principal",
                        is_admin=is_admin,
                    )
                    if item.page == pending_page
                ),
                None,
            )

            if pending_label is not None:
                st.session_state[
                    "tft_product_navigation"
                ] = pending_label

        labels = catalog.labels_for(
            "Principal",
            is_admin=is_admin,
        )

        current_choice = st.session_state.get(
            "tft_product_navigation"
        )
        if current_choice not in labels and labels:
            st.session_state["tft_product_navigation"] = labels[0]

        st.sidebar.markdown("#### Navegação")
        choice = st.sidebar.radio(
            "Navegação TFT Insight",
            options=labels,
            label_visibility="collapsed",
            key="tft_product_navigation",
        )

        page = catalog.page_from_label(choice)

        configured_api_url = os.getenv(
            "TFT_INSIGHT_API_BASE_URL",
            "http://127.0.0.1:8000",
        ).strip().rstrip("/")

        configured_api_key = os.getenv(
            "TFT_INSIGHT_API_KEY",
            "",
        ).strip() or None

        configured_environment = os.getenv(
            "TFT_INSIGHT_ENVIRONMENT",
            "Development",
        ).strip()

        if configured_environment.lower() == "production":
            api_base_url = configured_api_url
            api_key = configured_api_key
            environment = "Production"
        else:
            with st.sidebar.expander(
                "Configuração técnica",
                expanded=False,
            ):
                api_base_url = st.text_input(
                    "API Base URL",
                    value=configured_api_url,
                )
                api_key = st.text_input(
                    "API Key",
                    value=configured_api_key or "",
                    type="password",
                )
                environment = st.selectbox(
                    "Ambiente",
                    options=["Development", "Staging", "Production"],
                    index=(
                        1
                        if configured_environment.lower() == "staging"
                        else 0
                    ),
                )

        return cls(
            page=page,
            api_base_url=api_base_url.strip().rstrip("/"),
            api_key=api_key.strip() if isinstance(api_key, str) else api_key,
            environment=environment,
        )
'''


FILES["partner_platform/platform_core/router.py"] = r'''import streamlit as st


class PlatformRouter:
    def __init__(
        self,
        *,
        context,
        api_client,
        analytics,
    ) -> None:
        self.context = context
        self.api_client = api_client
        self.analytics = analytics

    def render(self) -> None:
        from partner_platform.pages import (
            admin_page,
            analytics_page,
            benchmark_page,
            home_page,
            developer_page,
            executive_page,
            explainability_page,
            overview_page,
            playground_page,
            prediction_page,
            settings_page,
        )

        routes = {
            "Home": lambda: home_page.render(
                context=self.context,
                api_client=self.api_client,
                analytics=self.analytics,
            ),
            "Overview": lambda: overview_page.render(
                context=self.context,
                api_client=self.api_client,
                analytics=self.analytics,
            ),
            "Executive": lambda: executive_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Playground": lambda: playground_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Benchmark": lambda: benchmark_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Prediction": lambda: prediction_page.render(
                context=self.context,
            ),
            "Explainability": lambda: explainability_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Analytics": lambda: analytics_page.render(
                context=self.context,
                analytics=self.analytics,
            ),
            "Developer": lambda: developer_page.render(
                context=self.context,
            ),
            "Settings": lambda: settings_page.render(
                context=self.context,
            ),
            "Admin": lambda: admin_page.render(
                context=self.context,
            ),
        }

        route = routes.get(self.context.page)

        if route is None:
            st.error(
                f"Página não registrada: {self.context.page}"
            )
            return

        route()
'''


print("=" * 88)
print("ROADMAP 28.1 - INSTALADOR AREA ADMIN")
print("=" * 88)

for relative, content in FILES.items():
    path = ROOT / relative

    if path.exists():
        backup_path = BACKUP / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    print(f"[OK] {relative}")

print("-" * 88)
print(f"Backup: {BACKUP}")
print("ROADMAP 28.1 INSTALADO.")