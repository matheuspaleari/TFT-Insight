from __future__ import annotations

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
)
from partner_platform.utils.display_names import (
    friendly_game_name,
    friendly_item_name,
    friendly_public_text,
)


def _items_line(values) -> str:
    if not isinstance(values, list):
        return "-"

    labels = [
        friendly_item_name(item)
        for item in values
        if str(item).strip()
    ]
    return " · ".join(labels) if labels else "-"


def _pct(value) -> str:
    return f"{float(value or 0.0):.1f}%"


def _placement(value) -> str:
    if value in (None, ""):
        return "-"
    return f"{value}º"


def _render_profile_summary(
    profile: dict,
    *,
    eyebrow: str,
    title: str,
) -> None:
    name = friendly_game_name(profile.get("character_id"))
    matches = int(profile.get("matches_played", 0) or 0)

    insight_banner(
        eyebrow=eyebrow,
        title=title,
        description=f"{name} · {matches} partida(s)",
        tone="neutral",
    )

    columns = st.columns(4)
    cards = (
        ("Uso", _pct(profile.get("usage_rate")), "Frequência no histórico", "◎"),
        (
            "Colocação média",
            f"{float(profile.get('average_placement', 0.0) or 0.0):.2f}",
            "Resultado observado",
            "◆",
        ),
        ("Top 4", _pct(profile.get("top4_rate")), "Taxa histórica", "↗"),
        (
            "Build completa",
            _pct(profile.get("full_build_rate")),
            (
                "Amostra comparável"
                if profile.get("eligible_for_comparison")
                else "Amostra exploratória"
            ),
            "◇",
        ),
    )

    for column, (label, value, caption, icon) in zip(columns, cards):
        with column:
            executive_card(
                title=label,
                value=value,
                caption=caption,
                icon=icon,
            )

    items = profile.get("most_used_items", [])
    if isinstance(items, list) and items:
        recurring = []
        for item in items[:5]:
            if not isinstance(item, dict):
                continue
            recurring.append(
                f"{friendly_item_name(item.get('item_id'))} "
                f"({_pct(item.get('match_rate'))})"
            )

        if recurring:
            with st.container(border=True):
                st.caption("Itens mais recorrentes")
                st.write(" · ".join(recurring))

    builds = profile.get("recurring_builds", [])
    if isinstance(builds, list) and builds:
        with st.expander("Ver builds recorrentes", expanded=False):
            for build in builds[:5]:
                if not isinstance(build, dict):
                    continue

                sample_label = (
                    "Amostra comparável"
                    if build.get("eligible_for_comparison")
                    else "Amostra exploratória"
                )

                st.write(
                    f"**{_items_line(build.get('item_ids', []))}**  \n"
                    f"{int(build.get('matches_played', 0) or 0)} partida(s) · "
                    f"colocação média "
                    f"{float(build.get('average_placement', 0.0) or 0.0):.2f} · "
                    f"Top 4 {_pct(build.get('top4_rate'))} · "
                    f"{sample_label}"
                )


def _render_latest(payload: dict) -> None:
    latest = payload.get("latest")
    if not isinstance(latest, dict):
        st.info(
            "A partida mais recente não teve um carry público validado. "
            "O TFT Insight não força uma escolha quando a evidência não é suficiente."
        )
        return

    st.markdown("#### Última partida")

    carry_name = friendly_game_name(latest.get("character_id"))
    item_ids = latest.get("item_ids", []) or []

    columns = st.columns(3)
    with columns[0]:
        executive_card(
            title="Carry",
            value=carry_name,
            caption="Identificado no board final",
            icon="◆",
        )
    with columns[1]:
        executive_card(
            title="Itens no carry",
            value=str(len(item_ids)),
            caption="Board final",
            icon="◎",
        )
    with columns[2]:
        executive_card(
            title="Colocação",
            value=_placement(latest.get("placement")),
            caption="Resultado da partida",
            icon="↗",
        )

    with st.container(border=True):
        st.caption("Itemização observada")
        st.write(_items_line(item_ids))


def render_carry_item_intelligence(
    payload: dict | None,
) -> None:
    """
    Roadmap 25.1 - Carries + Itens UX V2.

    O componente assume que a página externa já fornece o cabeçalho do módulo.
    A prioridade aqui é:
    1. leitura do Coach;
    2. última partida;
    3. padrão recorrente;
    4. evidências secundárias e limitações.
    """
    if not isinstance(payload, dict):
        return

    summary = payload.get("summary", {}) or {}
    coach = payload.get("coach", {}) or {}

    # 1. DECISÃO / LEITURA
    insight_banner(
        eyebrow="Leitura do Coach",
        title=friendly_public_text(
            str(
                coach.get(
                    "headline",
                    "Carries e itemizações no seu histórico",
                )
            )
        ),
        description=friendly_public_text(
            str(coach.get("latest_reading", "") or "")
        ),
        tone="neutral",
    )

    principle = str(
        coach.get("next_match_principle", "") or ""
    ).strip()

    if principle:
        insight_banner(
            eyebrow="Para a próxima partida",
            title="Use o padrão como referência, não como receita fixa",
            description=friendly_public_text(principle),
            tone="positive",
        )

    # 2. ÚLTIMA PARTIDA
    _render_latest(payload)

    # 3. PADRÃO PRINCIPAL
    st.markdown("#### Seu padrão de carry")

    most = payload.get("most_used_carry")
    best = payload.get("best_supported_carry")

    if isinstance(most, dict):
        _render_profile_summary(
            most,
            eyebrow="Mais recorrente",
            title="Carry mais usado no seu histórico",
        )
    else:
        st.caption(
            "Ainda não há um carry recorrente com amostra suficiente "
            "para formar um padrão principal."
        )

    if isinstance(best, dict):
        _render_profile_summary(
            best,
            eyebrow="Melhor histórico com amostra mínima",
            title="Melhor resultado entre os carries comparáveis",
        )
        st.caption(
            "O resultado descreve seu histórico recente. "
            "Ele não indica que esse carry seja a melhor escolha em qualquer lobby."
        )

    # 4. ITEMIZAÇÃO / QUALIDADE DA AMOSTRA
    st.markdown("#### Padrão de itemização")

    columns = st.columns(4)
    cards = (
        (
            "Build completa",
            _pct(summary.get("carry_full_item_rate")),
            "Carry com 3+ itens",
            "◇",
        ),
        (
            "Itens no carry",
            _pct(summary.get("carry_item_share")),
            "Participação dos itens",
            "◎",
        ),
        (
            "Itemização",
            f"{float(summary.get('itemization_score', 0.0) or 0.0):.1f}",
            str(summary.get("itemization_label", "-")),
            "◆",
        ),
        (
            "Detecção de carry",
            _pct(summary.get("carry_detection_rate")),
            (
                f"{summary.get('unique_carries', '-')} "
                "carry(s) diferentes"
            ),
            "↗",
        ),
    )

    for column, (label, value, caption, icon) in zip(columns, cards):
        with column:
            executive_card(
                title=label,
                value=value,
                caption=caption,
                icon=icon,
            )

    # 5. EVIDÊNCIAS SECUNDÁRIAS
    carries = payload.get("carries", [])
    if isinstance(carries, list) and carries:
        with st.expander("Ver outros carries", expanded=False):
            for index, profile in enumerate(carries[:10], 1):
                if not isinstance(profile, dict):
                    continue

                st.write(
                    f"**{index}. "
                    f"{friendly_game_name(profile.get('character_id'))}** · "
                    f"{int(profile.get('matches_played', 0) or 0)} partida(s) · "
                    f"colocação média "
                    f"{float(profile.get('average_placement', 0.0) or 0.0):.2f} · "
                    f"Top 4 {_pct(profile.get('top4_rate'))}"
                )

    observations = coach.get("observations", [])
    if isinstance(observations, list) and observations:
        with st.expander("O que o Coach observou", expanded=False):
            for item in observations[:4]:
                with st.container(border=True):
                    st.write(
                        friendly_public_text(str(item))
                    )

    with st.expander(
        "Como interpretar esta análise",
        expanded=False,
    ):
        seen = set()

        guardrails = list(coach.get("guardrails", []) or [])
        limitations = list(payload.get("limitations", []) or [])

        for item in guardrails + limitations:
            normalized = str(item).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                st.write(
                    "• " + friendly_public_text(normalized)
                )
