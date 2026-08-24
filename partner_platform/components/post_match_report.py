from __future__ import annotations

import streamlit as st

from partner_platform.components import (
    executive_card,
    insight_banner,
    section_header,
)



def _render_next_match_plan(report: dict) -> None:
    plan = report.get("next_match_plan", {}) or {}
    if not isinstance(plan, dict) or not plan:
        return

    section_header(
        "Plano para a próxima partida",
        subtitle=(
            "Uma prioridade clara para levar ao próximo jogo, "
            "já validada pelas proteções do Coach."
        ),
    )

    if not plan.get("publishable", False):
        insight_banner(
            eyebrow="Plano em revisão",
            title="O Coach segurou esta recomendação",
            description=str(
                plan.get("blocked_reason")
                or "A recomendação precisa de revisão antes de ser exibida."
            ),
            tone="neutral",
        )
        return

    focus = str(plan.get("active_skill_label", "") or "").strip()
    mission = str(plan.get("mission_title", "") or "").strip()
    objective = str(plan.get("mission_objective", "") or "").strip()

    if focus or mission:
        columns = st.columns(2)
        with columns[0]:
            executive_card(
                title="Foco",
                value=focus or "-",
                caption="Fundamento em treino",
                icon="◎",
            )
        with columns[1]:
            executive_card(
                title="Missão",
                value=mission or "-",
                caption="Objetivo da próxima partida",
                icon="◇",
            )

    insight_banner(
        eyebrow="Ação principal",
        title=str(plan.get("primary_title", "Próxima ação")),
        description=str(plan.get("primary_action", "")),
        tone="positive",
    )

    if objective:
        st.caption("Missão ativa")
        st.write(objective)

    watch_items = plan.get("watch_items", []) or []
    if isinstance(watch_items, list) and watch_items:
        st.markdown("#### Fique de olho")
        for item in watch_items[:2]:
            with st.container(border=True):
                st.write(str(item))

    preserve = str(plan.get("preserve", "") or "").strip()
    if preserve:
        insight_banner(
            eyebrow="Preserve",
            title=preserve,
            description=(
                "Mantenha este ponto forte enquanto treina a prioridade principal."
            ),
            tone="neutral",
        )

    reminder = str(plan.get("coach_reminder", "") or "").strip()
    if reminder:
        st.caption("Lembrete do Coach")
        st.write(reminder)


def render_post_match_report(report: dict | None) -> None:
    if not isinstance(report, dict):
        return

    match = report.get("match", {}) or {}

    section_header(
        "Sua última partida",
        subtitle=(
            "O que esta partida acrescenta ao seu treino atual, "
            "comparando o jogo com seu próprio histórico recente."
        ),
    )

    insight_banner(
        eyebrow="Pós-partida",
        title=str(report.get("headline", "Leitura da última partida")),
        description=str(report.get("summary", "")),
        tone="neutral",
    )

    columns = st.columns(4)
    values = (
        ("Colocação", f"{match.get('placement', '-')}º", "Última partida", "◆"),
        ("Nível final", str(match.get("level", "-")), "Progressão final", "↗"),
        ("Ouro restante", str(match.get("gold_left", "-")), "Fim da partida", "◈"),
        ("Dano ao lobby", str(match.get("total_damage_to_players", "-")), "Pressão observada", "◎"),
    )
    for column, (title, value, caption, icon) in zip(columns, values):
        with column:
            executive_card(
                title=title,
                value=value,
                caption=caption,
                icon=icon,
            )

    focus = report.get("focus_section", {}) or {}
    if focus:
        insight_banner(
            eyebrow="Seu foco",
            title=str(focus.get("title", "Foco de treino")),
            description=str(focus.get("text", "")),
            tone="neutral",
        )

    supporting = report.get("supporting_sections", [])
    if isinstance(supporting, list) and supporting:
        st.markdown("#### O que mais vale observar")
        for item in supporting:
            if isinstance(item, dict):
                with st.container(border=True):
                    st.markdown(f"**{item.get('title', 'Sinal')}**")
                    st.write(item.get("text", ""))

    # A orientação futura tem uma única fonte oficial na UI:
    # o Next Match Plan, já validado pelos Recommendation Guardrails.
    # coach_takeaway continua disponível no payload para auditoria/compatibilidade,
    # mas não é exibido como um segundo CTA para a próxima partida.
    _render_next_match_plan(report)

    missing = str(report.get("what_we_cannot_measure", "")).strip()
    if missing:
        with st.expander("O que ainda não conseguimos medir", expanded=False):
            st.write(missing)

    with st.expander("Detalhes técnicos da análise", expanded=False):
        internal = report.get("internal", {}) or {}
        protections = report.get("protections", {}) or {}
        st.caption(
            "Esses dados ajudam a auditar a leitura, "
            "mas não são necessários para usar o Coach."
        )
        st.json(
            {
                "verdict": internal.get("verdict"),
                "evidence_summary": internal.get("evidence_summary", {}),
                "historical_signals": internal.get("historical_signals", []),
                "protections": protections,
            }
        )
