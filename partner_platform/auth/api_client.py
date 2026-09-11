from __future__ import annotations

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
