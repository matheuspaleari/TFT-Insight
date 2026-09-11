from __future__ import annotations

import streamlit as st

from partner_platform.auth import api_client
from partner_platform.auth.session import store_auth


def _hide_portal_navigation() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"] {
            display: none !important;
        }

        html,
        body,
        [data-testid="stApp"],
        [data-testid="stAppViewContainer"] {
            background: #0E1117 !important;
        }

        .block-container {
            max-width: 640px;
            padding-top: 7vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth_page() -> None:
    _hide_portal_navigation()

    st.markdown("## TFT Insight")
    st.caption("Entre na sua conta ou crie um acesso.")

    tab_login, tab_register = st.tabs(
        ["Entrar", "Criar conta"]
    )

    with tab_login:
        with st.form(
            "tft_auth_login",
            clear_on_submit=False,
        ):
            email = st.text_input(
                "E-mail",
                key="tft_auth_login_email",
                autocomplete="email",
            )

            password = st.text_input(
                "Senha",
                type="password",
                key="tft_auth_login_password",
                autocomplete="current-password",
            )

            submitted = st.form_submit_button(
                "Entrar",
                width="stretch",
            )

        if submitted:
            try:
                payload = api_client.login(
                    email=email,
                    password=password,
                )

                store_auth(payload)
                st.rerun()

            except api_client.AuthApiError as exc:
                st.error(str(exc))

        st.caption(
            "Login com Google será adicionado na etapa 26.1D."
        )

    with tab_register:
        with st.form(
            "tft_auth_register",
            clear_on_submit=False,
        ):
            display_name = st.text_input(
                "Nome",
                key="tft_auth_register_name",
                autocomplete="name",
            )

            email = st.text_input(
                "E-mail",
                key="tft_auth_register_email",
                autocomplete="email",
            )

            password = st.text_input(
                "Senha",
                type="password",
                key="tft_auth_register_password",
                autocomplete="new-password",
                help=(
                    "Mínimo de 8 caracteres, com pelo menos "
                    "uma letra e um número."
                ),
            )

            password_confirmation = st.text_input(
                "Confirmar senha",
                type="password",
                key="tft_auth_register_password_confirmation",
                autocomplete="new-password",
            )

            submitted = st.form_submit_button(
                "Criar conta",
                width="stretch",
            )

        if submitted:
            if password != password_confirmation:
                st.error("As senhas não coincidem.")

            else:
                try:
                    payload = api_client.register(
                        email=email,
                        display_name=display_name,
                        password=password,
                    )

                    store_auth(payload)

                    st.success(
                        "Conta criada com sucesso."
                    )

                    st.rerun()

                except api_client.AuthApiError as exc:
                    st.error(str(exc))
