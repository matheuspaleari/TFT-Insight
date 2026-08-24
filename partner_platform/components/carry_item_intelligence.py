from __future__ import annotations

import re

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
    section_header,
)


def _friendly_id(
    value: str | None,
) -> str:
    text = str(
        value
        or ""
    ).strip()

    if not text:
        return "-"

    # Remove prefixos internos mais comuns.
    text = re.sub(
        r"^TFT\d+_",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"^TFT_",
        "",
        text,
        flags=re.IGNORECASE,
    )

    for prefix in (
        "Item_Artifact_",
        "Item_Radiant_",
        "Item_",
    ):
        if text.startswith(
            prefix
        ):
            text = text[
                len(prefix):
            ]

    text = text.replace(
        "_",
        " ",
    )

    text = re.sub(
        r"(?<=[a-z])(?=[A-Z])",
        " ",
        text,
    )

    # Limpeza de marcadores técnicos que vazam em alguns itens.
    replacements = {
        "TFT ": "",
        "Mod ": "",
    }

    for old, new in replacements.items():
        if text.startswith(
            old
        ):
            text = (
                new
                + text[
                    len(old):
                ]
            )

    return text.strip()


def _items_line(
    values,
) -> str:
    if not isinstance(
        values,
        list,
    ):
        return "-"

    labels = [
        _friendly_id(
            item
        )
        for item in values
        if str(item).strip()
    ]

    return (
        ", ".join(
            labels
        )
        if labels
        else "-"
    )


def _render_carry(
    profile: dict,
    *,
    eyebrow: str,
    title: str,
) -> None:
    insight_banner(
        eyebrow=eyebrow,
        title=title,
        description=(
            f"{_friendly_id(profile.get('character_id'))} · "
            f"{profile.get('matches_played', 0)} partida(s)"
        ),
        tone="neutral",
    )

    columns = st.columns(
        4
    )

    cards = (
        (
            "Uso",
            f"{float(profile.get('usage_rate', 0.0) or 0.0):.1f}%",
            "Frequência",
            "◎",
        ),
        (
            "Colocação média",
            f"{float(profile.get('average_placement', 0.0) or 0.0):.2f}",
            "Histórico observado",
            "◆",
        ),
        (
            "Top 4",
            f"{float(profile.get('top4_rate', 0.0) or 0.0):.1f}%",
            "Taxa histórica",
            "↗",
        ),
        (
            "Build completa",
            f"{float(profile.get('full_build_rate', 0.0) or 0.0):.1f}%",
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
        cards,
    ):
        with column:
            executive_card(
                title=card_title,
                value=value,
                caption=caption,
                icon=icon,
            )

    items = profile.get(
        "most_used_items",
        [],
    )

    if isinstance(
        items,
        list,
    ) and items:
        st.caption(
            "Itens mais recorrentes"
        )
        st.write(
            " · ".join(
                f"{_friendly_id(item.get('item_id'))} "
                f"({float(item.get('match_rate', 0.0) or 0.0):.1f}%)"
                for item in items[:5]
                if isinstance(
                    item,
                    dict,
                )
            )
        )

    builds = profile.get(
        "recurring_builds",
        [],
    )

    if isinstance(
        builds,
        list,
    ) and builds:
        with st.expander(
            "Builds observadas",
            expanded=False,
        ):
            for build in builds[:5]:
                if not isinstance(
                    build,
                    dict,
                ):
                    continue

                eligibility = (
                    "Elegível"
                    if build.get(
                        "eligible_for_comparison"
                    )
                    else "Exploratória"
                )

                st.write(
                    f"**{_items_line(build.get('item_ids', []))}** · "
                    f"{build.get('matches_played', 0)} partida(s) · "
                    f"média "
                    f"{float(build.get('average_placement', 0.0) or 0.0):.2f} · "
                    f"Top 4 "
                    f"{float(build.get('top4_rate', 0.0) or 0.0):.1f}% · "
                    f"{eligibility}"
                )


def render_carry_item_intelligence(
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
        "Carries e itens",
        subtitle=(
            "Leia primeiro o padrão de carry e itemização; depois use "
            "recorrência e resultados como evidência, não como receita fixa."
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
                "Carries e itemizações no seu histórico",
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
            title="Use histórico sem transformar build em receita",
            description=principle,
            tone="positive",
        )

    st.caption("Evidências do histórico")

    columns = st.columns(
        4
    )

    cards = (
        (
            "Carries identificados",
            str(
                summary.get(
                    "unique_carries",
                    "-",
                )
            ),
            (
                f"{float(summary.get('carry_detection_rate', 0.0) or 0.0):.1f}% "
                "das partidas"
            ),
            "◆",
        ),
        (
            "Itemização",
            f"{float(summary.get('itemization_score', 0.0) or 0.0):.1f}",
            str(
                summary.get(
                    "itemization_label",
                    "-",
                )
            ),
            "◇",
        ),
        (
            "Itens no carry",
            f"{float(summary.get('carry_item_share', 0.0) or 0.0):.1f}%",
            "Participação dos itens",
            "◎",
        ),
        (
            "Carry 3+ itens",
            f"{float(summary.get('carry_full_item_rate', 0.0) or 0.0):.1f}%",
            "Board final",
            "↗",
        ),
    )

    for column, (
        title,
        value,
        caption,
        icon,
    ) in zip(
        columns,
        cards,
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
    )

    if isinstance(
        latest,
        dict,
    ):
        st.markdown(
            "#### Última partida"
        )

        columns = st.columns(
            3
        )

        with columns[0]:
            executive_card(
                title="Carry",
                value=_friendly_id(
                    latest.get(
                        "character_id"
                    )
                ),
                caption="Identificado no board final",
                icon="◆",
            )

        with columns[1]:
            executive_card(
                title="Itens",
                value=str(
                    len(
                        latest.get(
                            "item_ids",
                            [],
                        )
                        or []
                    )
                ),
                caption="No carry",
                icon="◎",
            )

        with columns[2]:
            executive_card(
                title="Colocação",
                value=(
                    f"{latest.get('placement', '-')}º"
                ),
                caption="Resultado da partida",
                icon="↗",
            )

        with st.container(
            border=True
        ):
            st.write(
                "**Itens do carry:** "
                + _items_line(
                    latest.get(
                        "item_ids",
                        [],
                    )
                )
            )

    most = payload.get(
        "most_used_carry"
    )

    if isinstance(
        most,
        dict,
    ):
        _render_carry(
            most,
            eyebrow="Mais usado",
            title="Seu carry mais recorrente",
        )

    best = payload.get(
        "best_supported_carry"
    )

    if isinstance(
        best,
        dict,
    ):
        _render_carry(
            best,
            eyebrow="Melhor histórico com amostra mínima",
            title=(
                "Melhor desempenho entre carries elegíveis"
            ),
        )

        st.caption(
            "Isso descreve o histórico recente; não significa "
            "que esse carry seja a melhor escolha para qualquer lobby."
        )

    carries = payload.get(
        "carries",
        [],
    )

    if isinstance(
        carries,
        list,
    ) and carries:
        with st.expander(
            "Ver outros carries",
            expanded=False,
        ):
            for index, profile in enumerate(
                carries[:10],
                1,
            ):
                if not isinstance(
                    profile,
                    dict,
                ):
                    continue

                st.write(
                    f"**{index}. {_friendly_id(profile.get('character_id'))}** · "
                    f"{profile.get('matches_played', 0)} partida(s) · "
                    f"média "
                    f"{float(profile.get('average_placement', 0.0) or 0.0):.2f} · "
                    f"Top 4 "
                    f"{float(profile.get('top4_rate', 0.0) or 0.0):.1f}%"
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
