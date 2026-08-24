from __future__ import annotations

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
    section_header,
)


def _safe_float(
    value,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def render_economy_intelligence(
    payload: dict | None,
) -> None:
    if not isinstance(
        payload,
        dict,
    ):
        return

    summary = payload.get(
        "summary",
        {},
    ) or {}

    section_header(
        "Economia",
        subtitle=(
            "Entenda primeiro o padrão econômico que o histórico sustenta; "
            "depois confira nível, ouro e recorrência como evidências."
        ),
    )

    coach = payload.get(
        "coach",
        {},
    ) or {}

    insight_banner(
        eyebrow="Leitura do Coach",
        title=str(
            coach.get(
                "headline",
                "Como sua economia termina nas partidas",
            )
        ),
        description=str(
            coach.get(
                "latest_reading",
                "",
            )
        ),
        tone="neutral",
    )

    principle = str(
        coach.get(
            "next_match_principle",
            "",
        )
        or ""
    ).strip()

    if principle:
        insight_banner(
            eyebrow="Decisão para a próxima partida",
            title="Planeje antes do próximo gasto grande",
            description=principle,
            tone="positive",
        )


    st.caption("Evidências do histórico")

    columns = st.columns(4)

    cards = (
        (
            "Economia",
            f"{_safe_float(summary.get('score')):.1f}",
            str(summary.get("label", "-")),
            "◇",
        ),
        (
            "Nível médio",
            f"{_safe_float(summary.get('average_level')):.2f}",
            f"Mediana {_safe_float(summary.get('median_level')):.1f}",
            "↗",
        ),
        (
            "Ouro restante",
            f"{_safe_float(summary.get('average_gold_left')):.1f}",
            f"Mediana {_safe_float(summary.get('median_gold_left')):.1f}",
            "◎",
        ),
        (
            "Nível 9+",
            f"{_safe_float(summary.get('level_9_rate')):.1f}%",
            "Frequência no histórico",
            "◆",
        ),
    )

    for column, (
        title,
        value,
        caption,
        icon,
    ) in zip(columns, cards):
        with column:
            executive_card(
                title=title,
                value=value,
                caption=caption,
                icon=icon,
            )

    latest = payload.get(
        "latest",
        {},
    ) or {}

    st.markdown(
        "#### Última partida"
    )

    latest_columns = st.columns(4)

    latest_cards = (
        (
            "Colocação",
            f"{latest.get('placement', '-')}º",
            "Resultado final",
            "◆",
        ),
        (
            "Nível",
            str(latest.get("level", "-")),
            "Progressão final",
            "↗",
        ),
        (
            "Ouro",
            str(latest.get("gold_left", "-")),
            "Restante no fim",
            "◎",
        ),
        (
            "Round",
            str(latest.get("last_round", "-")),
            "Último round",
            "◇",
        ),
    )

    for column, (
        title,
        value,
        caption,
        icon,
    ) in zip(
        latest_columns,
        latest_cards,
    ):
        with column:
            executive_card(
                title=title,
                value=value,
                caption=caption,
                icon=icon,
            )

    distribution = payload.get(
        "distribution",
        {},
    ) or {}

    st.markdown(
        "#### Estados finais recorrentes"
    )

    dist_columns = st.columns(2)

    with dist_columns[0]:
        with st.container(border=True):
            st.markdown(
                "**Nível final**"
            )
            st.write(
                f"Nível 7 ou menos: **{distribution.get('level_7_or_lower', 0)}** partida(s)"
            )
            st.write(
                f"Nível 8: **{distribution.get('level_8', 0)}** partida(s)"
            )
            st.write(
                f"Nível 9+: **{distribution.get('level_9_plus', 0)}** partida(s)"
            )

    with dist_columns[1]:
        with st.container(border=True):
            st.markdown(
                "**Ouro restante**"
            )
            st.write(
                f"0–5: **{distribution.get('gold_0_to_5', 0)}** partida(s)"
            )
            st.write(
                f"6–19: **{distribution.get('gold_6_to_19', 0)}** partida(s)"
            )
            st.write(
                f"20+: **{distribution.get('gold_20_plus', 0)}** partida(s)"
            )
            st.caption(
                "As faixas descrevem o estado final e não dizem "
                "se gastar ou guardar foi correto."
            )

    trend = payload.get(
        "recent_trend",
        {},
    ) or {}

    st.markdown(
        "#### Histórico recente"
    )

    if trend.get(
        "signal"
    ) == "HISTORICO_INSUFICIENTE":
        with st.container(border=True):
            st.write(
                "Ainda não há histórico suficiente para comparar "
                "dois blocos recentes."
            )
    else:
        with st.container(border=True):
            st.write(
                f"Nível médio: **{_safe_float(trend.get('previous_average_level')):.2f} → "
                f"{_safe_float(trend.get('recent_average_level')):.2f}**"
            )
            st.write(
                f"Ouro final médio: **{_safe_float(trend.get('previous_average_gold_left')):.2f} → "
                f"{_safe_float(trend.get('recent_average_gold_left')):.2f}**"
            )
            st.write(
                f"Colocação média: **{_safe_float(trend.get('previous_average_placement')):.2f} → "
                f"{_safe_float(trend.get('recent_average_placement')):.2f}**"
            )
            st.caption(
                "A comparação descreve os blocos históricos; não "
                "identifica qual decisão causou a mudança."
            )

    comparison = payload.get(
        "placement_comparison",
        {},
    ) or {}

    st.markdown(
        "#### Nível 9+ e resultado"
    )

    if comparison.get(
        "eligible_for_comparison"
    ):
        with st.container(border=True):
            st.write(
                f"Nível 9+: **{_safe_float(comparison.get('level_9_plus_average_placement')):.2f}** "
                f"de colocação média em "
                f"{comparison.get('level_9_plus_matches', 0)} partida(s)."
            )
            st.write(
                f"Abaixo do nível 9: **{_safe_float(comparison.get('below_level_9_average_placement')):.2f}** "
                f"em {comparison.get('below_level_9_matches', 0)} partida(s)."
            )
            st.caption(
                "Essa associação não significa que Fast 9 seja "
                "automaticamente a melhor decisão."
            )
    else:
        with st.container(border=True):
            st.write(
                "Ainda não há pelo menos 3 partidas nos dois grupos "
                "para comparar nível 9+ com segurança."
            )

    observations = coach.get(
        "observations",
        [],
    )

    if isinstance(
        observations,
        list,
    ) and observations:
        st.markdown(
            "#### O que o Coach observa"
        )

        for item in observations[:4]:
            with st.container(border=True):
                st.write(
                    str(item)
                )

    with st.expander(
        "Como interpretar esta análise",
        expanded=False,
    ):
        seen = set()

        for item in (
            list(
                coach.get(
                    "guardrails",
                    [],
                )
                or []
            )
            + list(
                payload.get(
                    "limitations",
                    [],
                )
                or []
            )
        ):
            normalized = str(
                item
            ).strip()

            if (
                normalized
                and normalized not in seen
            ):
                seen.add(
                    normalized
                )
                st.write(
                    "• "
                    + normalized
                )
