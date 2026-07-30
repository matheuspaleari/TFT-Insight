"""
Dashboard web do TFT Insight Performance Score.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from PIL import Image

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOGO = Image.open(
    PROJECT_ROOT / "assets" / "LOGO.png"
)

CRYSTAL = Image.open(
    PROJECT_ROOT / "assets" / "crystal.png"
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config import Config
from src.services.player_analysis_service import PlayerAnalysisService


st.set_page_config(
    page_title="TFT Insight Performance Score",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def apply_custom_theme() -> None:
    """
    Carrega o tema CSS.
    """

    theme_css = (
        PROJECT_ROOT
        / "styles"
        / "theme.css"
    ).read_text(
        encoding="utf-8"
    )

    home_css = (
        PROJECT_ROOT
        / "styles"
        / "home.css"
    ).read_text(
        encoding="utf-8"
    )

    st.markdown(
        f"<style>{theme_css}\n{home_css}</style>",
        unsafe_allow_html=True
    )

STATUS_HELP = (
    "Representa o desempenho geral de todas as partidas analisadas. "
    "O score considera colocação média, Top 4, vitórias, nível e dano."
)

TREND_HELP = (
    "Compara o período mais recente com o anterior. Um jogador pode "
    "ter status Muito Bom e estar Em queda, ou ser Regular e estar "
    "Evoluindo."
)


def initialize_state() -> None:
    """Inicializa os dados persistidos durante a sessão."""

    defaults = {
        "analysis_data": None,
        "searched_game_name": "",
        "searched_tag_line": "",
        "searched_match_count": 20,
        "use_custom_reference": False,
        "reference_game_name": Config.MASTER_GAME_NAME or "",
        "reference_tag_line": Config.MASTER_TAG_LINE or "",
        "current_view": "home",
        "selected_priority": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_search_form(
) -> tuple[str, str, str, str, int] | None:
    """Exibe o formulário para pesquisar jogador e referência."""

    with st.sidebar:
        st.header("Pesquisar jogador")
        st.caption("Informe o nome e a tag do Riot ID.")

        with st.form("player_search_form"):
            game_name = st.text_input(
                "Nome do jogador",
                value=st.session_state["searched_game_name"],
                placeholder="Ex.: Pinador Doss"
            )

            tag_line = st.text_input(
                "Tag",
                value=st.session_state["searched_tag_line"],
                placeholder="Ex.: 000"
            )

            match_count = st.select_slider(
                "Quantidade de partidas",
                options=[20, 50, 100],
                value=st.session_state["searched_match_count"]
            )

            st.divider()
            st.subheader("Jogador de referência")

            use_custom_reference = st.checkbox(
                "Usar referência personalizada",
                value=st.session_state["use_custom_reference"],
                help=(
                    "Desmarcado, usa o jogador padrão configurado "
                    "no arquivo .env."
                )
            )

            if use_custom_reference:
                reference_game_name = st.text_input(
                    "Nome da referência",
                    value=st.session_state["reference_game_name"],
                    placeholder="Ex.: kingfelpx"
                )

                reference_tag_line = st.text_input(
                    "Tag da referência",
                    value=st.session_state["reference_tag_line"],
                    placeholder="Ex.: br1"
                )
            else:
                reference_game_name = Config.MASTER_GAME_NAME or ""
                reference_tag_line = Config.MASTER_TAG_LINE or ""

                st.info(
                    "Referência padrão: "
                    f"{reference_game_name}#{reference_tag_line}"
                )

            submitted = st.form_submit_button(
                "Analisar jogador",
                use_container_width=True,
                type="primary"
            )

        st.caption(
            "A primeira análise pode demorar porque as partidas são "
            "consultadas na Riot API."
        )

        if not submitted:
            return None

        game_name = game_name.strip()
        tag_line = tag_line.strip().removeprefix("#")
        reference_game_name = reference_game_name.strip()
        reference_tag_line = (
            reference_tag_line.strip().removeprefix("#")
        )

        if not game_name or not tag_line:
            st.error("Informe o nome e a tag do jogador.")
            return None

        if not reference_game_name or not reference_tag_line:
            st.error("Informe o nome e a tag da referência.")
            return None

        if (
            game_name.casefold() == reference_game_name.casefold()
            and tag_line.casefold() == reference_tag_line.casefold()
        ):
            st.error(
                "O jogador analisado e a referência devem ser diferentes."
            )
            return None

        st.session_state["searched_game_name"] = game_name
        st.session_state["searched_tag_line"] = tag_line
        st.session_state["searched_match_count"] = match_count
        st.session_state["use_custom_reference"] = use_custom_reference
        st.session_state["reference_game_name"] = reference_game_name
        st.session_state["reference_tag_line"] = reference_tag_line

        return (
            game_name,
            tag_line,
            reference_game_name,
            reference_tag_line,
            match_count,
        )


def run_player_analysis(
    game_name: str,
    tag_line: str,
    reference_game_name: str,
    reference_tag_line: str,
    match_count: int
) -> dict[str, Any]:
    """Executa a análise completa."""

    service = PlayerAnalysisService(
        reference_game_name=reference_game_name,
        reference_tag_line=reference_tag_line
    )

    return service.analyze(
        game_name=game_name,
        tag_line=tag_line,
        match_count=match_count
    )


def get_impact_score(insight: dict[str, Any]) -> int:
    """Obtém um score de impacto de 0 a 100."""

    if "impact_score" in insight:
        return max(0, min(int(insight["impact_score"]), 100))

    fallback = {5: 100, 4: 80, 3: 60, 2: 40, 1: 20}
    return fallback.get(int(insight.get("severity", 1)), 20)



DEMO_PLAYER = {
    "game_name": "Pinador Doss",
    "tag_line": "000",
    "score": 77,
    "status_icon": "🟡",
    "status_label": "Bom",
    "matches": 9,
    "lp": "+32",
    "evolution": "📈 Forte",
}

DEMO_PRIORITIES = [
    {
        "rank": "🥇",
        "title": "Economia",
        "impact": 12,
        "priority": "Alta prioridade",
        "player_value": "28 de ouro",
        "benchmark_value": "42 de ouro",
        "reason": (
            "Você costuma gastar ouro cedo demais durante o Stage 3. "
            "Isso reduz sua força quando chega ao nível 8."
        ),
        "actions": [
            "Não role abaixo de 30 de ouro.",
            "Priorize uma sequência consistente de vitórias ou derrotas.",
            "Planeje o nível 8 para o Stage 4-2.",
        ],
    },
    {
        "rank": "🥈",
        "title": "Scout",
        "impact": 6,
        "priority": "Média prioridade",
        "player_value": "Baixa frequência",
        "benchmark_value": "Alta frequência",
        "reason": (
            "Você reage tarde a adversários contestando suas unidades "
            "e costuma ajustar o posicionamento apenas no fim da partida."
        ),
        "actions": [
            "Observe pelo menos três adversários por rodada.",
            "Confirme se sua composição está sendo contestada.",
            "Ajuste o posicionamento antes de cada combate importante.",
        ],
    },
    {
        "rank": "🥉",
        "title": "Flexibilidade",
        "impact": 3,
        "priority": "Oportunidade",
        "player_value": "Baixa adaptação",
        "benchmark_value": "Alta adaptação",
        "reason": (
            "Você mantém a mesma direção por muitas rodadas, mesmo quando "
            "a loja e os itens favorecem uma composição diferente."
        ),
        "actions": [
            "Defina duas linhas de composição antes do Stage 3.",
            "Use seus itens para escolher a direção final.",
            "Abandone uma composição quando ela estiver muito contestada.",
        ],
    },
]


def go_to_home() -> None:
    """
    Retorna para a visão resumida.
    """

    st.session_state["current_view"] = "home"


def go_to_details() -> None:
    """
    Abre a análise detalhada.
    """

    st.session_state["current_view"] = "details"


def open_priority_popup(priority_index: int) -> None:
    """Abre o painel flutuante de uma prioridade."""

    st.session_state["selected_priority"] = priority_index


def close_priority_popup() -> None:
    """Fecha o painel flutuante."""

    st.session_state["selected_priority"] = None


def render_priority_popup() -> None:
    """
    Exibe um painel fixo no canto inferior direito da aplicação.

    Diferente de st.dialog, este painel não ocupa o centro da tela e
    mantém a Home visível ao fundo, simulando um companion app.
    """

    selected_index = st.session_state.get("selected_priority")

    if selected_index is None:
        return

    priority = DEMO_PRIORITIES[selected_index]

    with st.container(key="coach_floating_popup"):
        header_left, header_right = st.columns(
            [5, 1],
            vertical_alignment="center"
        )

        with header_left:
            st.markdown(
                f"### {priority['rank']} {priority['title']}"
            )
            st.caption(priority["priority"])

        with header_right:
            st.button(
                "✕",
                key="close_floating_popup",
                help="Fechar",
                on_click=close_priority_popup
            )

        impact_column, benchmark_column = st.columns(2)

        impact_column.metric(
            "Impacto esperado",
            f"+{priority['impact']} Score"
        )

        benchmark_column.metric(
            "Benchmark",
            "Top 10 Challenger"
        )

        st.markdown("#### Comparação")
        comparison_left, comparison_right = st.columns(2)
        comparison_left.metric("Você", priority["player_value"])
        comparison_right.metric(
            "Top 10",
            priority["benchmark_value"]
        )

        st.markdown("#### 🤖 Coach AI")
        st.info(priority["reason"])

        st.markdown("#### Como melhorar")
        for action in priority["actions"]:
            st.write(f"✓ {action}")

        st.button(
            "Entendi",
            use_container_width=True,
            type="primary",
            key=f"understood_{selected_index}",
            on_click=close_priority_popup
        )

def render_commercial_home() -> None:
    """
    Exibe a home comercial resumida.

    Nesta primeira versão os dados são demonstrativos para validar
    o fluxo, os cartões e os modais antes de ligar às métricas reais.
    """

    player_name = (
        f"{DEMO_PLAYER['game_name']}"
        f"#{DEMO_PLAYER['tag_line']}"
    )

    top_left, top_right = st.columns(
        [8, 1],
        vertical_alignment="center"
    )

    with top_left:
        st.caption("TFT Insight AI")
        st.markdown(f"# {player_name}")

    with top_right:
        st.image(CRYSTAL, width=58)

    st.caption(
        "Protótipo comercial — dados demonstrativos para validar a UX."
    )

    st.markdown(
        '<div class="home-section-title">Sua Performance</div>',
        unsafe_allow_html=True
    )

    score_column, status_column = st.columns(
        [1.2, 1],
        vertical_alignment="center"
    )

    with score_column:
        st.markdown(
            f"""
            <div class="home-score-card">
                <span class="home-score-value">
                    {DEMO_PLAYER['score']}
                </span>
                <span class="home-score-total">/100</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with status_column:
        st.markdown(
            f"""
            <div class="home-status-card">
                <span class="home-status-dot">
                    {DEMO_PLAYER['status_icon']}
                </span>
                <span class="home-status-label">
                    {DEMO_PLAYER['status_label']}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()
    st.subheader("Resumo da sessão")

    session_columns = st.columns(4)

    session_columns[0].metric(
        "🎮 Partidas",
        DEMO_PLAYER["matches"]
    )

    session_columns[1].metric(
        "📈 LP",
        DEMO_PLAYER["lp"]
    )

    session_columns[2].metric(
        "⭐ Performance",
        DEMO_PLAYER["score"]
    )

    session_columns[3].metric(
        "📊 Evolução",
        DEMO_PLAYER["evolution"]
    )

    st.divider()
    st.subheader("🎯 Hoje você pode melhorar")

    for index, priority in enumerate(DEMO_PRIORITIES):
        with st.container(border=True):
            title_column, impact_column, action_column = st.columns(
                [4, 1.5, 1],
                vertical_alignment="center"
            )

            with title_column:
                st.markdown(
                    f"### {priority['rank']} {priority['title']}"
                )
                st.caption(priority["priority"])

            with impact_column:
                st.metric(
                    "Impacto",
                    f"+{priority['impact']} Score"
                )

            with action_column:
                st.button(
                    "Ver detalhes",
                    key=f"priority_{index}",
                    use_container_width=True,
                    on_click=open_priority_popup,
                    args=(index,)
                )

    render_priority_popup()

    st.divider()
    st.subheader("🤖 Coach AI")

    st.info(
        "Você evoluiu sua economia nas últimas partidas. "
        "Seu próximo salto de desempenho virá ao preservar mais ouro "
        "até o nível 7 e escolher melhor o momento de estabilizar o board."
    )

    st.button(
        "🔍 Ver análise completa",
        use_container_width=True,
        type="primary",
        on_click=go_to_details
    )


def render_welcome() -> None:
    """Exibe a tela inicial antes da pesquisa."""

    st.image(LOGO, width=420)
    st.write(
        "Pesquise qualquer jogador de Teamfight Tactics utilizando "
        "o Riot ID."
    )
    st.info(
        "Abra a barra lateral, informe o nome, a tag e clique em "
        "**Analisar jogador**."
    )


def render_header(data: dict[str, Any]) -> None:
    """
    Exibe o cabeçalho da análise.
    """

    player = data["searched_player"]

    left, right = st.columns(
        [14, 1],
        vertical_alignment="center"
    )

    with left:

        st.caption(
            "Análise de desempenho, evolução e oportunidades de melhoria."
        )

        st.subheader(
            f"{player['game_name']}#{player['tag_line']}"
        )

    with right:

        st.image(
            CRYSTAL,
            width=54
        )



def render_performance_cards(
    performance: dict[str, Any],
    trend: dict[str, Any]
) -> None:
    """Exibe Score, Status e Tendência."""

    score = int(performance["performance_score"])
    status = performance["status"]
    score_column, status_column, trend_column = st.columns(3)

    with score_column:
        st.metric(
            "TFT Insight Performance Score",
            f"{score}/100"
        )
        st.progress(score, text=f"Performance geral: {score}/100")

    with status_column:
        st.metric(
            "Status",
            f"{status['icon']} {status['label']}",
            help=STATUS_HELP
        )
        st.caption(status.get("description", "Desempenho geral."))

    with trend_column:
        st.metric(
            "Tendência",
            f"{trend['icon']} {trend['label']}",
            help=TREND_HELP
        )
        st.caption(trend["description"])


def render_player_summary(summary: dict[str, Any]) -> None:
    """Exibe as principais métricas do jogador."""

    st.subheader("Resumo do jogador")
    columns = st.columns(4)
    columns[0].metric("Partidas", summary["matches_played"])
    columns[1].metric(
        "Colocação média",
        summary["average_placement"],
        help="Quanto menor, melhor."
    )
    columns[2].metric("Top 4", f"{summary['top4_rate']}%")
    columns[3].metric("Vitórias", f"{summary['win_rate']}%")

    columns = st.columns(3)
    columns[0].metric("Nível médio", summary["average_level"])
    columns[1].metric("Dano médio", summary["average_damage"])
    columns[2].metric(
        "Ouro restante médio",
        summary["average_gold_left"]
    )


def render_trend_details(trend: dict[str, Any]) -> None:
    """Exibe a comparação entre períodos."""

    st.subheader("Evolução recente")

    if not trend["has_enough_data"]:
        st.info(trend["description"])
        return

    previous = trend["previous"]
    recent = trend["recent"]

    st.write(
        f"Comparação de **{trend['matches_per_period']} partidas** "
        "em cada período."
    )

    previous_column, recent_column = st.columns(2)

    with previous_column:
        st.markdown("#### Período anterior")
        st.metric("Colocação média", previous["average_placement"])
        st.metric("Top 4", f"{previous['top4_rate']}%")
        st.metric("Nível médio", previous["average_level"])
        st.metric("Dano médio", previous["average_damage"])

    with recent_column:
        st.markdown("#### Período recente")
        st.metric(
            "Colocação média",
            recent["average_placement"],
            delta=round(
                previous["average_placement"]
                - recent["average_placement"],
                2
            )
        )
        st.metric(
            "Top 4",
            f"{recent['top4_rate']}%",
            delta=(
                f"{round(recent['top4_rate'] - previous['top4_rate'], 2)} "
                "p.p."
            )
        )
        st.metric(
            "Nível médio",
            recent["average_level"],
            delta=round(
                recent["average_level"]
                - previous["average_level"],
                2
            )
        )
        st.metric(
            "Dano médio",
            recent["average_damage"],
            delta=round(
                recent["average_damage"]
                - previous["average_damage"],
                2
            )
        )

    with st.expander("ⓘ Entenda a tendência"):
        st.write(trend["description"])
        for detail in trend.get("details", []):
            st.write(f"• {detail}")


def render_comparison(comparison: dict[str, Any]) -> None:
    """Exibe a comparação com o jogador referência."""

    st.subheader("Comparação com jogador referência")
    player = comparison["player_one"]
    reference = comparison["player_two"]
    player_name = f"{player['game_name']}#{player['tag_line']}"
    reference_name = f"{reference['game_name']}#{reference['tag_line']}"

    metrics = [
        ("Colocação média", "average_placement", ""),
        ("Top 4", "top4_rate", "%"),
        ("Vitórias", "win_rate", "%"),
        ("Nível médio", "average_level", ""),
        ("Dano médio", "average_damage", ""),
    ]

    for label, key, suffix in metrics:
        label_column, player_column, reference_column = st.columns(
            [1.3, 1, 1]
        )
        label_column.write(f"**{label}**")
        player_column.metric(player_name, f"{player[key]}{suffix}")
        reference_column.metric(
            reference_name,
            f"{reference[key]}{suffix}"
        )


def render_player_insights(insights: list[str]) -> None:
    """Exibe a análise geral."""

    st.subheader("Análise geral")
    if not insights:
        st.success("Não foram encontradas diferenças relevantes.")
        return

    for insight in insights:
        st.write(f"• {insight}")


def render_coach(insights: list[dict[str, Any]]) -> None:
    """Exibe oportunidades de melhoria."""

    st.subheader("Coach — maiores oportunidades")

    if not insights:
        st.success("Nenhuma oportunidade relevante foi encontrada.")
        return

    for position, insight in enumerate(insights[:5], start=1):
        impact_score = get_impact_score(insight)

        with st.container(border=True):
            st.markdown(f"### {position}. {insight['trait_name']}")
            st.write(f"**Impacto:** {insight['impact']}")
            st.progress(
                impact_score,
                text=f"Impacto estimado: {impact_score}/100"
            )

            player_column, reference_column = st.columns(2)

            with player_column:
                st.markdown("**Você**")
                st.write(f"Partidas: {insight['player_one_uses']}")
                st.write(
                    "Colocação média: "
                    f"{insight['player_one_average_placement']}"
                )
                st.write(f"Top 4: {insight['player_one_top4_rate']}%")

            with reference_column:
                st.markdown("**Referência**")
                st.write(f"Partidas: {insight['player_two_uses']}")
                st.write(
                    "Colocação média: "
                    f"{insight['player_two_average_placement']}"
                )
                st.write(f"Top 4: {insight['player_two_top4_rate']}%")

            st.info(f"**Análise:** {insight['analysis']}")
            st.warning(
                f"**Recomendação:** {insight['recommendation']}"
            )


def render_traits_table(traits: list[dict[str, Any]]) -> None:
    """Exibe traits em uma tabela."""

    if not traits:
        st.info("Nenhuma trait encontrada.")
        return

    rows = [
        {
            "Trait": trait["trait_name"],
            "Usos": trait["times_used"],
            "Colocação média": trait["average_placement"],
            "Top 4 (%)": trait["top4_rate"],
            "Vitórias (%)": trait["win_rate"],
            "Média de unidades": trait["average_units"],
        }
        for trait in traits
    ]

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


def render_traits_tabs(data: dict[str, Any]) -> None:
    """Exibe traits dos dois jogadores em abas."""

    searched = data["searched_player"]
    reference = data["reference_player"]

    st.subheader("Traits dos jogadores")
    player_tab, reference_tab = st.tabs(
        [
            f"Você — {searched['game_name']}#{searched['tag_line']}",
            (
                f"Referência — {reference['game_name']}"
                f"#{reference['tag_line']}"
            ),
        ]
    )

    with player_tab:
        render_traits_table(data["player_traits"])

    with reference_tab:
        render_traits_table(data["master_traits"])


def render_extraction_summary(extraction: dict[str, Any]) -> None:
    """Exibe informações técnicas da atualização."""

    with st.expander("Detalhes da atualização"):
        for label, result in (
            ("Jogador pesquisado", extraction["player"]),
            ("Jogador referência", extraction["reference"]),
        ):
            st.markdown(f"#### {label}")
            st.write(f"Partidas encontradas: {result['match_ids_found']}")
            st.write(f"Novas partidas: {result['saved_count']}")
            st.write(f"Já existentes: {result['existing_count']}")

            if result["failed_matches"]:
                st.warning(
                    "Algumas partidas ficaram pendentes por limite "
                    "ou falha temporária da API."
                )


def render_dashboard(data: dict[str, Any]) -> None:
    """Renderiza todas as seções."""

    render_header(data)
    render_performance_cards(data["performance"], data["trend"])
    st.divider()
    render_player_summary(data["player_summary"])
    st.divider()
    render_trend_details(data["trend"])
    st.divider()
    render_comparison(data["comparison"])
    st.divider()
    render_player_insights(data["player_insights"])
    st.divider()
    render_coach(data["trait_insights"])
    st.divider()
    render_traits_tabs(data)
    st.divider()
    render_extraction_summary(data["extraction"])


def main() -> None:
    """
    Inicializa a aplicação.
    """

    apply_custom_theme()
    initialize_state()

    if st.session_state["current_view"] == "home":
        render_commercial_home()
        return

    back_column, _ = st.columns([1, 5])

    with back_column:
        st.button(
            "← Voltar ao resumo",
            use_container_width=True,
            on_click=go_to_home
        )

    search = render_search_form()

    if search is not None:
        (
            game_name,
            tag_line,
            reference_game_name,
            reference_tag_line,
            match_count,
        ) = search

        try:
            with st.spinner(
                "Atualizando partidas e calculando métricas..."
            ):
                data = run_player_analysis(
                    game_name=game_name,
                    tag_line=tag_line,
                    reference_game_name=reference_game_name,
                    reference_tag_line=reference_tag_line,
                    match_count=match_count
                )

            st.session_state["analysis_data"] = data

        except Exception as error:
            st.session_state["analysis_data"] = None
            st.error("Não foi possível analisar os jogadores.")
            st.exception(error)

    data = st.session_state["analysis_data"]

    if data is None:
        render_welcome()
        return

    render_dashboard(data)


if __name__ == "__main__":
    main()
