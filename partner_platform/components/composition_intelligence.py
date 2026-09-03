from __future__ import annotations

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
    section_header,
)
from partner_platform.utils.display_names import (
    friendly_game_name,
    friendly_public_text,
)


def _join_ids(
    values,
) -> str:
    if not isinstance(
        values,
        list,
    ):
        return "-"

    labels = [
        friendly_game_name(
            item
        )
        for item in values
        if str(
            item
        ).strip()
    ]

    return (
        ", ".join(
            labels
        )
        if labels
        else "-"
    )


def _confidence_text(
    profile: dict,
) -> str:
    confidence = profile.get(
        "statistical_confidence",
        {},
    ) or {}

    score = float(
        confidence.get(
            "score",
            0.0,
        )
        or 0.0
    )

    level = str(
        confidence.get(
            "level",
            "-",
        )
        or "-"
    )

    return (
        f"{level} · {score:.1f}%"
    )


def _render_profile(
    *,
    profile: dict,
    title: str,
    eyebrow: str,
) -> None:
    carry = friendly_game_name(
        profile.get(
            "carry_character_id"
        )
    )
    tank = friendly_game_name(
        profile.get(
            "tank_character_id"
        )
    )

    description = (
        f"Carry: {carry} · "
        f"Tank: {tank} · "
        f"{profile.get('matches_played', 0)} partida(s)"
    )

    insight_banner(
        eyebrow=eyebrow,
        title=title,
        description=description,
        tone="neutral",
    )

    columns = st.columns(
        4
    )

    values = (
        (
            "Uso",
            f"{float(profile.get('usage_rate', 0.0) or 0.0):.1f}%",
            "Frequência no histórico",
            "◎",
        ),
        (
            "Colocação média",
            f"{float(profile.get('average_placement', 0.0) or 0.0):.2f}",
            "Resultado observado",
            "◆",
        ),
        (
            "Top 4",
            f"{float(profile.get('top4_rate', 0.0) or 0.0):.1f}%",
            "Taxa histórica",
            "↗",
        ),
        (
            "Confiança",
            _confidence_text(
                profile
            ),
            (
                "Elegível para comparação"
                if profile.get(
                    "eligible_for_comparison"
                )
                else "Amostra exploratória"
            ),
            "◇",
        ),
    )

    for column, (
        card_title,
        value,
        caption,
        icon,
    ) in zip(
        columns,
        values,
    ):
        with column:
            executive_card(
                title=card_title,
                value=value,
                caption=caption,
                icon=icon,
            )

    st.caption(
        "Traits principais"
    )
    st.write(
        _join_ids(
            profile.get(
                "primary_trait_names",
                [],
            )
        )
    )

    st.caption(
        "Núcleo observado"
    )
    st.write(
        _join_ids(
            profile.get(
                "core_unit_ids",
                [],
            )
        )
    )


def render_composition_intelligence(
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
        "Composições",
        subtitle=(
            "Entenda seu padrão de composição primeiro; depois use "
            "as evidências para decidir quando repetir, explorar ou adaptar."
        ),
    )

    coach = payload.get(
        "coach",
        {},
    ) or {}

    insight_banner(
        eyebrow="Leitura do Coach",
        title=friendly_public_text(
            str(
                coach.get(
                    "headline",
                    "Seu histórico de composições",
                )
            )
        ),
        description=friendly_public_text(
            str(
                summary.get(
                    "repetition_interpretation",
                    "",
                )
            )
        ),
        tone="neutral",
    )

    st.caption("Evidências do histórico")

    columns = st.columns(
        4
    )

    values = (
        (
            "Partidas",
            str(
                summary.get(
                    "matches_analyzed",
                    "-",
                )
            ),
            "Histórico analisado",
            "◆",
        ),
        (
            "Composições",
            str(
                summary.get(
                    "unique_compositions",
                    "-",
                )
            ),
            "Estruturas identificadas",
            "◇",
        ),
        (
            "Diversidade",
            f"{float(summary.get('diversity_rate', 0.0) or 0.0):.1f}%",
            "Variedade de estruturas",
            "◎",
        ),
        (
            "Repetição",
            f"{float(summary.get('repetition_rate', 0.0) or 0.0):.1f}%",
            "Recorrência no histórico",
            "↻",
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

    most_used = payload.get(
        "most_used",
        {},
    ) or {}

    if most_used:
        _render_profile(
            profile=most_used,
            eyebrow="Mais usada",
            title=(
                "Sua estrutura mais recorrente"
            ),
        )

    best = payload.get(
        "best_supported",
    )

    if isinstance(
        best,
        dict,
    ) and best:
        _render_profile(
            profile=best,
            eyebrow=(
                "Melhor resultado com amostra mínima"
            ),
            title=(
                "Melhor desempenho histórico entre "
                "as composições elegíveis"
            ),
        )
        st.caption(
            "Isso descreve o histórico recente e não significa "
            "que essa composição seja a melhor escolha para qualquer lobby."
        )

    compositions = payload.get(
        "compositions",
        [],
    )

    if isinstance(
        compositions,
        list,
    ) and compositions:
        with st.expander(
            "Ver outras composições identificadas",
            expanded=False,
        ):
            for index, profile in enumerate(
                compositions[:8],
                1,
            ):
                if not isinstance(
                    profile,
                    dict,
                ):
                    continue

                carry = friendly_game_name(
                    profile.get(
                        "carry_character_id"
                    )
                )

                eligibility = (
                    "Elegível"
                    if profile.get(
                        "eligible_for_comparison"
                    )
                    else "Exploratória"
                )

                st.markdown(
                    f"**{index}. {carry}** · "
                    f"{profile.get('matches_played', 0)} partida(s) · "
                    f"média "
                    f"{float(profile.get('average_placement', 0.0) or 0.0):.2f} · "
                    f"Top 4 "
                    f"{float(profile.get('top4_rate', 0.0) or 0.0):.1f}% · "
                    f"{eligibility}"
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

        for item in observations[:3]:
            with st.container(
                border=True
            ):
                st.write(
                    friendly_public_text(
                        str(item)
                    )
                )

    limitations = payload.get(
        "limitations",
        [],
    )

    guardrails = coach.get(
        "guardrails",
        [],
    )

    if (
        isinstance(
            limitations,
            list,
        )
        and limitations
    ) or (
        isinstance(
            guardrails,
            list,
        )
        and guardrails
    ):
        with st.expander(
            "Como interpretar esta análise",
            expanded=False,
        ):
            for item in (
                list(
                    guardrails
                    if isinstance(
                        guardrails,
                        list,
                    )
                    else []
                )
                + list(
                    limitations
                    if isinstance(
                        limitations,
                        list,
                    )
                    else []
                )
            ):
                st.write(
                    "• "
                    + friendly_public_text(
                        str(item)
                    )
                )
