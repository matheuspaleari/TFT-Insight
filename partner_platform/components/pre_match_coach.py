from __future__ import annotations

import streamlit as st

from partner_platform.components import insight_banner, section_header
from partner_platform.utils.display_names import friendly_game_name, friendly_public_text


def build_pre_match_coach(*, training: dict, composition: dict, contest: dict, economy: dict, carry_item: dict) -> dict:
    """Consolida sinais já calculados. Não cria analytics nem troca a missão."""
    skill = str(training.get("skill_label") or training.get("skill_id") or "Foco atual")
    mission = str(training.get("mission_title") or "Missão atual")
    objective = str(training.get("objective") or "").strip()

    comp_summary = composition.get("summary", {}) or {}
    comp_most = composition.get("most_used", {}) or {}
    contest_summary = contest.get("summary", {}) or {}
    economy_summary = economy.get("summary", {}) or {}
    carry_summary = carry_item.get("summary", {}) or {}
    carry_most = carry_item.get("most_used_carry", {}) or {}

    support = []
    diversity = float(comp_summary.get("diversity_rate", 0.0) or 0.0)
    repetition = float(comp_summary.get("repetition_rate", 0.0) or 0.0)
    if comp_summary:
        support.append({
            "label": "Composições",
            "text": (
                f"{int(comp_summary.get('unique_compositions', 0) or 0)} estruturas em "
                f"{int(comp_summary.get('matches_analyzed', 0) or 0)} partidas; "
                f"diversidade {diversity:.1f}% e repetição {repetition:.1f}%. "
                "Use o histórico como contexto; repetição não prova intenção de forçar composição."
            ),
        })

    if contest_summary:
        support.append({
            "label": "Contestação",
            "text": (
                f"Carry contestado em {float(contest_summary.get('carry_contest_rate', 0.0) or 0.0):.1f}% "
                f"do histórico; alta contestação em {float(contest_summary.get('high_contest_rate', 0.0) or 0.0):.1f}%. "
                "Trate contestação como sinal para decidir, não como ordem automática de pivot."
            ),
        })

    if economy_summary:
        support.append({
            "label": "Economia",
            "text": (
                f"Nível final médio {float(economy_summary.get('average_level', 0.0) or 0.0):.2f}; "
                f"nível 9+ em {float(economy_summary.get('level_9_rate', 0.0) or 0.0):.1f}% e "
                f"ouro final médio {float(economy_summary.get('average_gold_left', 0.0) or 0.0):.1f}. "
                "Esses são estados finais e não revelam timing de XP, roll ou gasto."
            ),
        })

    if carry_summary:
        carry_name = friendly_game_name(carry_most.get("character_id")) if carry_most else "-"
        carry_matches = int(carry_most.get("matches_played", 0) or 0) if carry_most else 0
        carry_text = (
            f"Carry mais recorrente: {carry_name} em {carry_matches} partida(s). "
            if carry_matches else
            "Ainda não há carry recorrente com amostra útil. "
        )
        carry_text += (
            f"Carry com 3+ itens em {float(carry_summary.get('carry_full_item_rate', 0.0) or 0.0):.1f}% das partidas. "
            "Build histórica não é receita obrigatória."
        )
        support.append({"label": "Carries e itens", "text": carry_text})

    # A ação principal vem da missão existente; os módulos avançados apenas dão contexto.
    if objective:
        primary_action = objective
    elif "level" in skill.lower():
        primary_action = "Antes do próximo gasto grande, defina se você vai subir de nível, estabilizar ou preservar recursos."
    else:
        primary_action = f"Execute a missão “{mission}” como sua única prioridade de treino nesta partida."

    return {
        "skill": skill,
        "mission": mission,
        "primary_action": primary_action,
        "support": support,
        "preserve": "Mantenha o que já funciona no seu jogo; os sinais históricos não substituem a leitura do lobby atual.",
        "guardrails": [
            "A consolidação não altera sua prioridade de aprendizado.",
            "A consolidação não altera sua missão ativa.",
            "Histórico e associação não são tratados como causalidade.",
            "Nenhuma decisão não observada pela telemetria é inventada.",
            "Composição, contestação, economia e itens são contexto de apoio, não quatro novas missões.",
        ],
    }


def render_pre_match_coach(payload: dict) -> None:
    section_header(
        "Coach pré-partida",
        subtitle="Uma prioridade para levar ao próximo jogo, apoiada pelo seu histórico recente.",
    )

    cols = st.columns(2)
    with cols[0]:
        insight_banner(
            eyebrow="FOCO",
            title=friendly_public_text(str(payload.get("skill", "-"))),
            description="Fundamento que continua guiando seu treino.",
            tone="neutral",
        )
    with cols[1]:
        insight_banner(
            eyebrow="MISSÃO",
            title=friendly_public_text(str(payload.get("mission", "-"))),
            description="A consolidação não troca sua missão ativa.",
            tone="neutral",
        )

    insight_banner(
        eyebrow="AÇÃO PRINCIPAL",
        title="Leve uma decisão clara para a próxima partida",
        description=friendly_public_text(str(payload.get("primary_action", ""))),
        tone="success",
    )

    st.markdown("#### Contexto que apoia sua decisão")
    for item in payload.get("support", []):
        with st.container(border=True):
            st.markdown(f"**{item.get('label', 'Sinal')}**")
            st.write(friendly_public_text(str(item.get("text", ""))))

    st.markdown("#### Preserve")
    st.write(friendly_public_text(str(payload.get("preserve", ""))))

    with st.expander("Como interpretar este plano"):
        for item in payload.get("guardrails", []):
            st.write("• " + friendly_public_text(str(item)))
