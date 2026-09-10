from __future__ import annotations

import os

import streamlit as st

from partner_platform.auth import api_client


_TOKEN_KEY = "tft_auth_token"
_USER_KEY = "tft_auth_user"


def auth_enabled() -> bool:
    raw = os.getenv("TFT_INSIGHT_AUTH_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def authenticated() -> bool:
    return bool(
        st.session_state.get(_TOKEN_KEY)
        and st.session_state.get(_USER_KEY)
    )


def current_user() -> dict | None:
    user = st.session_state.get(_USER_KEY)
    return user if isinstance(user, dict) else None


def store_auth(payload: dict) -> None:
    token = str(payload.get("access_token", "")).strip()
    user = payload.get("user")

    if not token or not isinstance(user, dict):
        raise api_client.AuthApiError("Resposta de login inválida.")

    st.session_state[_TOKEN_KEY] = token
    st.session_state[_USER_KEY] = user


def clear_session() -> None:
    st.session_state.pop(_TOKEN_KEY, None)
    st.session_state.pop(_USER_KEY, None)


def validate_existing_session() -> bool:
    token = str(st.session_state.get(_TOKEN_KEY, "")).strip()
    if not token:
        clear_session()
        return False

    try:
        payload = api_client.me(token)
        user = payload.get("user")
        if not isinstance(user, dict):
            clear_session()
            return False
        st.session_state[_USER_KEY] = user
        return True
    except api_client.AuthApiError:
        clear_session()
        return False


def require_auth() -> bool:
    if not auth_enabled():
        return True

    if not authenticated():
        return False

    return validate_existing_session()
