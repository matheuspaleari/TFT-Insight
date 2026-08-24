from __future__ import annotations

import re

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
    section_header,
)


def _friendly_id(value):
    text = str(
        value
        or ""
    ).strip()

    if not text:
        return "-"

    text = re.sub(
        r"^TFT\d+_",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace(
        "_",
        " ",
    )

    text = re.sub(
        r"(?<=[a-z])(?=[A-Z])",
        " ",
        text,
    )

    return text.strip()


def _frequency_lines(values):
    if not isinstance(
        values,
        list,
    ) or not values:
        st.caption(
            "Nenhum sinal recorrente suficiente."
        )
        return

    for item in values[:5]:
        if not isinstance(
            item,
            dict,
        ):
            continue

        st.write(
            f"**{_friendly_id(item.get('item_id'))}** · "
            f"{item.get('matches_observed', 0)} partida(s) · "
            f"{float(item.get('match_rate', 0.0) or 0.0):.1f}%"
        )


def render_contest_intelligence(
    payload,
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

    coach = payload.get(
        "coach",
        {},
    ) or {}

    section_header(
        "Contestação",
        subtitle=(
            "Leia primeiro onde a disputa merece atenção; depois confira "
            "as evidências antes de comprometer recursos no próximo lobby."
        ),
    )

    # ------------------------------------------------------------------
    # Roadmap 22.6B
    # Leitura e decisão aparecem antes dos números detalhados.
    # ------------------------------------------------------------------
    insight_banner(
        eyebrow="Leitura do Coach",
        title=str(
            coach.get(
                "headline",
                "Como a disputa aparece no seu histórico",
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
            title="Use contestação como sinal, não como ordem",
            description=principle,
            tone="positive",
        )

    st.caption(
        "Evidências do histórico"
    )

    columns = st.columns(
        4
    )

    values = (
        (
            "Contestação média",
            f"{float(summary.get('average_score', 0.0) or 0.0):.1f}",
            str(
                summary.get(
                    "level",
                    "-",
                )
            ),
            "◎",
        ),
        (
            "Alta contestação",
            f"{float(summary.get('high_contest_rate', 0.0) or 0.0):.1f}%",
            "Partidas acima de 60",
            "↗",
        ),
        (
            "Carry contestado",
            f"{float(summary.get('carry_contest_rate', 0.0) or 0.0):.1f}%",
            "Frequência no histórico",
            "◆",
        ),
        (
            "Rivais no carry",
            f"{float(summary.get('average_opponents_contesting_carry', 0.0) or 0.0):.2f}",
            "Média por partida",
            "◇",
        ),
    )

    for column, (
        title,
        value,
        caption,
        icon,
    ) in zip(
        columns,
        values,
    ):
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

    if latest:
        st.markdown(
            "#### Última partida"
        )

        cols = st.columns(
            3
        )

        latest_values = (
            (
                "Índice",
                f"{float(latest.get('score', 0.0) or 0.0):.1f}",
                str(
                    latest.get(
                        "level",
                        "-",
                    )
                ),
                "◎",
            ),
            (
                "Carry",
                _friendly_id(
                    latest.get(
                        "carry_character_id"
                    )
                ),
                (
                    "Contestado"
                    if latest.get(
                        "carry_contested"
                    )
                    else "Sem contestação direta"
                ),
                "◆",
            ),
            (
                "Adversários no carry",
                str(
                    latest.get(
                        "opponents_contesting_carry",
                        0,
                    )
                ),
                "Board final",
                "↗",
            ),
        )

        for col, args in zip(
            cols,
            latest_values,
        ):
            with col:
                executive_card(
                    title=args[0],
                    value=args[1],
                    caption=args[2],
                    icon=args[3],
                )

    recurring = payload.get(
        "recurring_pressure",
        {},
    ) or {}

    st.markdown(
        "#### Pressões recorrentes"
    )

    cols = st.columns(
        2
    )

    with cols[0]:
        with st.container(
            border=True
        ):
            st.markdown(
                "**Unidades que mais aparecem disputadas**"
            )

            _frequency_lines(
                recurring.get(
                    "units",
                    [],
                )
            )

    with cols[1]:
        with st.container(
            border=True
        ):
            st.markdown(
                "**Traits que mais aparecem compartilhadas**"
            )

            _frequency_lines(
                recurring.get(
                    "traits",
                    [],
                )
            )

    comparison = payload.get(
        "placement_comparison",
        {},
    ) or {}

    st.markdown(
        "#### Contestação e resultado"
    )

    if comparison.get(
        "eligible_for_comparison"
    ):
        high = comparison.get(
            "high_contest_average_placement"
        )

        lower = comparison.get(
            "lower_contest_average_placement"
        )

        with st.container(
            border=True
        ):
            st.write(
                f"Alta contestação: **{float(high):.2f}** de colocação média · "
                f"Menor contestação: **{float(lower):.2f}**."
            )

            st.caption(
                "Essa diferença descreve associação histórica; "
                "não prova que a contestação causou o resultado."
            )

    else:
        with st.container(
            border=True
        ):
            st.write(
                "Ainda não há pelo menos 3 partidas nos dois grupos "
                "para comparar colocação com segurança."
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
            with st.container(
                border=True
            ):
                st.write(
                    str(
                        item
                    )
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
                and normalized
                not in seen
            ):
                seen.add(
                    normalized
                )

                st.write(
                    "• "
                    + normalized
                )
