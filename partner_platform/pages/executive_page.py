import streamlit as st

from partner_platform.components import (
    empty_state,
    executive_reading,
    executive_spotlight,
    player_badge,
    premium_kpi,
    section_header,
    summary_row,
    technical_details,
)
from partner_platform.intelligence import (
    build_executive_v2,
    build_kpi_explanations,
)
from partner_platform.platform_core import PlatformPage
from partner_platform.session import PlayerSessionStore
from partner_platform.ui import friendly_exception


def _fmt(
    value,
    *,
    suffix: str = "",
    decimals: int = 1,
) -> str:
    if value is None:
        return "N/A"

    if isinstance(
        value,
        float,
    ):
        return f"{value:.{decimals}f}{suffix}"

    return f"{value}{suffix}"


def render(
    *,
    context,
    api_client,
) -> None:
    current = (
        PlayerSessionStore.current()
    )

    page = PlatformPage(
        title="Painel executivo",
        subtitle=(
            "Executive Intelligence para score, benchmark, "
            "previsão e próxima ação."
        ),
        environment=context.environment,
        platform_version=context.platform_version,
        hero_badges=(
            "Current Player",
            "Benchmark",
            "Explainable",
            "Previsão",
        ),
    )

    page.begin()

    if current is None:
        empty_state(
            title="Nenhum jogador ativo",
            description=(
                "Analise um jogador na área de análise. "
                "O Executive reutilizará a sessão automaticamente."
            ),
            icon="▣",
        )
        page.end()
        return

    report = current.analysis_report
    benchmark = current.benchmark_report

    try:
        if report is None:
            with st.spinner(
                "Carregando análise do Current Player..."
            ):
                report = api_client.analyze_player(
                    game_name=current.game_name,
                    tag_line=current.tag_line,
                    match_count=current.match_count,
                    learn=False,
                )

            PlayerSessionStore.save_analysis(
                report,
                game_name=current.game_name,
                tag_line=current.tag_line,
                region=current.region,
                match_count=current.match_count,
            )

        if benchmark is None:
            with st.spinner(
                "Carregando benchmark do Current Player..."
            ):
                benchmark = (
                    api_client
                    .compare_player_to_challenger(
                        game_name=current.game_name,
                        tag_line=current.tag_line,
                        match_count=current.match_count,
                        region=current.region,
                    )
                )

            PlayerSessionStore.save_benchmark(
                benchmark
            )

    except Exception as error:
        friendly_exception(
            error,
            context="a visão executiva",
        )
        page.end()
        return

    analysis = report.get(
        "analysis",
        report,
    )

    summary = build_executive_v2(
        analysis=analysis,
        benchmark=benchmark,
    )

    explanations = build_kpi_explanations(
        analysis=analysis,
        benchmark=benchmark,
        matches_analyzed=current.match_count,
    )

    player_badge(
        game_name=current.game_name,
        tag_line=current.tag_line,
        region=current.region,
        match_count=current.match_count,
    )

    cards = st.columns(5)

    items = (
        (
            "Score",
            _fmt(summary["overall_score"]),
            summary["classification"],
            "◆",
            explanations["score"],
        ),
        (
            "Top 4",
            _fmt(
                summary["top4_probability"],
                suffix="%",
            ),
            "Previsão",
            "↗",
            explanations["top4"],
        ),
        (
            "Confidence",
            _fmt(
                summary["confidence"],
                suffix="%",
            ),
            summary["confidence_label"],
            "✦",
            explanations["confidence"],
        ),
        (
            "Benchmark",
            _fmt(
                summary["benchmark_percentile"]
            ),
            summary["benchmark_classification"],
            "♛",
            explanations["benchmark"],
        ),
        (
            "Expected",
            _fmt(
                summary["expected_placement"],
                decimals=2,
            ),
            "Placement",
            "▦",
            explanations["expected"],
        ),
    )

    for column, item in zip(
        cards,
        items,
    ):
        with column:
            detail = item[4]

            premium_kpi(
                title=item[0],
                value=item[1],
                caption=item[2],
                icon=item[3],
                explanation_title=detail["title"],
                explanation_body=detail["body"],
                factors=detail["factors"],
                technical_note=detail["note"],
            )

    executive_reading(
        title=f"{current.game_name} em uma frase",
        body=summary["executive_reading"],
    )

    section_header(
        "Decision snapshot",
        subtitle=(
            "Strength, opportunity e ação prioritária."
        ),
    )

    snapshot = st.columns(3)

    strength = summary["strength"]
    opportunity = summary["opportunity"]

    with snapshot[0]:
        executive_spotlight(
            eyebrow="TOP STRENGTH",
            title=strength["label"],
            value=(
                "Percentile "
                + _fmt(
                    strength["percentile"]
                )
            ),
            description=(
                "Maior diferencial atual em relação "
                "à distribuição Challenger."
            ),
            tone="positive",
            symbol="🏆",
        )

    with snapshot[1]:
        executive_spotlight(
            eyebrow="TOP OPPORTUNITY",
            title=opportunity["label"],
            value=(
                "Percentile "
                + _fmt(
                    opportunity["percentile"]
                )
            ),
            description=(
                "Principal dimensão com espaço de evolução "
                "contra a referência Challenger."
            ),
            tone="warning",
            symbol="⚠",
        )

    with snapshot[2]:
        executive_spotlight(
            eyebrow="NEXT ACTION",
            title="Prioridade",
            value=summary["next_action"],
            description=(
                "Ação prática derivada da recomendação "
                "e do Coach atual."
            ),
            tone="neutral",
            symbol="🎯",
        )

    section_header(
        "Coach",
        subtitle=(
            "Contexto prático associado à análise executiva."
        ),
    )

    summary_row(
        label="Ponto de atenção",
        value=(
            summary["attention"]
            or "Não informado"
        ),
        description=(
            "O que deve ser monitorado antes "
            "de comprometer a linha."
        ),
    )

    summary_row(
        label="Condição de vitória",
        value=(
            summary["win_condition"]
            or "Não informada"
        ),
        description=(
            "Condição principal para maximizar "
            "o resultado esperado."
        ),
    )

    technical_details(
        {
            "analysis": report,
            "benchmark": benchmark,
            "executive_summary": summary,
        },
        title="Detalhes técnicos executivos",
    )

    page.end()
