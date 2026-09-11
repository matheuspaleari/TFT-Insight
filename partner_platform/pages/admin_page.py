from __future__ import annotations

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
