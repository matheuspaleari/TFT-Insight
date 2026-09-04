from datetime import datetime

import streamlit as st

from partner_platform.session import PlayerSessionStore
from partner_platform.ui import render_html


def _time_label(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except Exception:
        return "—"


def current_session_panel() -> None:
    session = PlayerSessionStore.current()
    st.sidebar.markdown("#### Jogador")

    if session is None:
        render_html(
            """
            <div class="tft-current-session tft-current-session-empty">
                <div class="tft-current-session-title">Nenhum jogador ativo</div>
                <div class="tft-current-session-caption">
                    Informe seu Riot ID na página Análise.
                </div>
            </div>
            """,
            sidebar=True,
        )
        return

    render_html(
        f"""
        <div class="tft-current-session">
            <div class="tft-current-session-kicker">JOGADOR ATUAL</div>
            <div class="tft-current-session-title">{session.game_name}</div>
            <div class="tft-current-session-tag">#{session.tag_line}</div>
            <div class="tft-current-session-meta">
                {session.match_count} partidas · atualizado {_time_label(session.updated_at)}
            </div>
        </div>
        """,
        sidebar=True,
    )

    history = PlayerSessionStore.recent()
    if history:
        with st.sidebar.expander("Jogadores recentes", expanded=False):
            for index, item in enumerate(history):
                if st.button(
                    f"{item['game_name']} #{item['tag_line']}",
                    key=f"restore_player_{index}",
                    width="stretch",
                ):
                    PlayerSessionStore.restore(index)
                    st.rerun()

    if st.sidebar.button(
        "Trocar jogador",
        width="stretch",
    ):
        PlayerSessionStore.clear()
        st.session_state.pop("benchmark_comparison", None)
        st.session_state.pop("benchmark_comparison_key", None)
        st.rerun()
