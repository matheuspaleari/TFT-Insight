import streamlit as st

from partner_platform.components import (
    empty_state,
    executive_card,
    loading_screen,
    technical_details,
)
from partner_platform.platform_core import PlatformPage
from partner_platform.session import PlayerSessionStore
from partner_platform.ui import friendly_exception


def render(
    *,
    context,
    api_client,
) -> None:
    (
        default_name,
        default_tag,
        default_matches,
    ) = PlayerSessionStore.current_defaults()

    page = PlatformPage(
        title="Área de análise do jogador",
        subtitle=(
            "Analise uma vez e reutilize o jogador "
            "em toda a Partner Platform."
        ),
        environment=context.environment,
        platform_version=context.platform_version,
        hero_badges=(
            "Player Context",
            "Riot API",
            "Cache",
            "Previsão",
        ),
    )

    page.begin()

    left, right = st.columns(
        [1, 1.4]
    )

    with left:
        with st.form(
            "platform-playground"
        ):
            game_name = st.text_input(
                "Riot ID",
                value=default_name,
            )
            tag_line = st.text_input(
                "Tag",
                value=default_tag,
            )
            match_count = st.slider(
                "Matches",
                1,
                100,
                default_matches,
            )
            learn = st.toggle(
                "Update Learning",
                value=True,
            )

            submitted = (
                st.form_submit_button(
                    "Analyze",
                    width="stretch",
                )
            )

    with right:
        current = (
            PlayerSessionStore.current()
        )

        if (
            not submitted
            and current
            and current.analysis_report
        ):
            report = (
                current.analysis_report
            )

            st.success(
                f"Current Session · "
                f"{current.riot_id}"
            )

        elif not submitted:
            empty_state(
                title="Ready to analyze",
                description=(
                    "A primeira análise cria o Current Player. "
                    "Benchmark, Explainability e Executive "
                    "reutilizam essa sessão."
                ),
                icon="⚡",
            )
            page.end()
            return

        else:
            placeholder = st.empty()

            with placeholder.container():
                loading_screen(
                    title="Analisando jogador",
                    message=(
                        "Salvando Analysis e identidade "
                        "na sessão atual."
                    ),
                )

            try:
                report = (
                    api_client.analyze_player(
                        game_name=game_name,
                        tag_line=tag_line,
                        match_count=match_count,
                        learn=learn,
                    )
                )
            except Exception as error:
                placeholder.empty()
                friendly_exception(
                    error,
                    context="a análise do jogador",
                )
                page.end()
                return

            placeholder.empty()

            PlayerSessionStore.save_analysis(
                report,
                game_name=game_name,
                tag_line=tag_line,
                match_count=match_count,
            )

        analysis = report.get(
            "analysis",
            {},
        )
        prediction = analysis.get(
            "prediction",
            {},
        )

        cards = st.columns(3)

        with cards[0]:
            executive_card(
                title="Overall score",
                value=(
                    f"{analysis.get('overall_score', 0):.1f}"
                ),
                caption=analysis.get(
                    "classification",
                    "Analysis",
                ),
                icon="◆",
            )

        with cards[1]:
            executive_card(
                title="Top 4",
                value=(
                    f"{prediction.get('top4_probability', 0):.1f}%"
                ),
                caption=prediction.get(
                    "risk",
                    "Previsão",
                ),
                icon="↗",
            )

        with cards[2]:
            executive_card(
                title="Confidence",
                value=(
                    f"{prediction.get('confidence', 0):.1f}%"
                ),
                caption=(
                    "Expected "
                    f"{prediction.get('expected_placement', 0):.2f}"
                ),
                icon="✦",
            )

        coach = analysis.get(
            "coach",
            {},
        )

        if coach.get(
            "pregame_attention"
        ):
            st.warning(
                coach["pregame_attention"]
            )

        if coach.get(
            "win_condition"
        ):
            st.success(
                coach["win_condition"]
            )

        technical_details(
            report,
            title=(
                "Detalhes técnicos · "
                "Raw API response"
            ),
        )

    page.end()
