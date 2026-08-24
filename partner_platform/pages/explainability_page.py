from typing import Any
import streamlit as st
from partner_platform.components import (
    decision_step, empty_state, evidence_card, executive_card,
    insight_banner, loading_screen, section_header, technical_details
)
from partner_platform.intelligence import build_explainability_narrative
from partner_platform.platform_core import PlatformPage
from partner_platform.session import PlayerSessionStore
from partner_platform.ui import friendly_exception

def _fmt(value: Any, suffix: str = "") -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}{suffix}" if isinstance(value, float) else f"{value}{suffix}"

def render(*, context, api_client) -> None:
    current = PlayerSessionStore.current()
    page = PlatformPage(
        title="Explainability Premium",
        subtitle="A explicação acompanha automaticamente o Current Player.",
        environment=context.environment,
        platform_version=context.platform_version,
        hero_badges=("Current Player", "Why", "Evidence", "Coach Context"),
    )
    page.begin()

    if current is None:
        empty_state(
            title="Nenhum jogador ativo",
            description="Analise um jogador primeiro na área de análise.",
            icon="◎",
            action_hint="A análise será reutilizada automaticamente aqui.",
        )
        page.end()
        return

    report = current.analysis_report

    if report is None:
        placeholder = st.empty()
        with placeholder.container():
            loading_screen(
                title="Construindo explicação",
                message=f"Carregando análise de {current.riot_id}.",
            )
        try:
            report = api_client.analyze_player(
                game_name=current.game_name,
                tag_line=current.tag_line,
                match_count=current.match_count,
                learn=False,
            )
        except Exception as error:
            placeholder.empty()
            friendly_exception(error, context="a explicação da análise")
            page.end()
            return
        placeholder.empty()
        PlayerSessionStore.save_analysis(
            report,
            game_name=current.game_name,
            tag_line=current.tag_line,
            region=current.region,
            match_count=current.match_count,
        )

    st.success(f"Current Player · {current.riot_id} · {current.match_count} matches")

    analysis = report.get("analysis", report)
    prediction = analysis.get("prediction", {})
    narrative = build_explainability_narrative(analysis)

    cols = st.columns(4)
    values = [
        ("Overall score", _fmt(analysis.get("overall_score")), analysis.get("classification", "Analysis"), "◆"),
        ("Top 4", _fmt(prediction.get("top4_probability"), "%"), "Probabilidade prevista", "↗"),
        ("Confiança", _fmt(prediction.get("confidence"), "%"), "Confiança da previsão", "✦"),
        ("Colocação esperada", _fmt(prediction.get("expected_placement")), prediction.get("risk", "Previsão"), "♛"),
    ]
    for column, (title, value, caption, icon) in zip(cols, values):
        with column:
            executive_card(title=title, value=value, caption=caption, icon=icon)

    section_header("Why this recommendation?", subtitle="Narrativa derivada da análise atual.")
    insight_banner(
        eyebrow="Recommendation",
        title=narrative["recommendation"],
        description=narrative["confidence_text"],
        tone="positive",
    )

    left, right = st.columns(2)
    with left:
        insight_banner(
            eyebrow="Pre-game attention",
            title="O que observar",
            description=narrative["attention"],
            tone="warning",
        )
    with right:
        insight_banner(
            eyebrow="Win condition",
            title="Condição de vitória",
            description=narrative["win_condition"],
            tone="positive",
        )

    section_header("Evidence", subtitle="Sinais públicos da análise.")
    evidence_cols = st.columns(len(narrative["evidence"]))
    for column, item in zip(evidence_cols, narrative["evidence"]):
        with column:
            evidence_card(
                title=item["label"],
                value=item["value"],
                description="Sinal observado na análise atual.",
                status=item["tone"],
            )

    section_header("Decision path", subtitle="Caminho resumido até a recomendação.")
    path_items = narrative["evidence"] + [{
        "label": "Recommendation",
        "value": narrative["recommendation"],
        "tone": "positive",
    }]
    for index, item in enumerate(path_items):
        decision_step(
            label=item["label"],
            value=item["value"],
            state=item["tone"],
            last=index == len(path_items) - 1,
        )

    technical_details(report, title="Detalhes técnicos · Resposta bruta da API")
    page.end()
