import streamlit as st


class PlatformRouter:
    def __init__(
        self,
        *,
        context,
        api_client,
        analytics,
    ) -> None:
        self.context = context
        self.api_client = api_client
        self.analytics = analytics

    def render(self) -> None:
        from partner_platform.pages import (
            analytics_page,
            benchmark_page,
            home_page,
            developer_page,
            executive_page,
            explainability_page,
            overview_page,
            playground_page,
            prediction_page,
            settings_page,
        )

        routes = {
            "Home": lambda: home_page.render(
                context=self.context,
                api_client=self.api_client,
                analytics=self.analytics,
            ),
            "Overview": lambda: overview_page.render(
                context=self.context,
                api_client=self.api_client,
                analytics=self.analytics,
            ),
            "Executive": lambda: executive_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Playground": lambda: playground_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Benchmark": lambda: benchmark_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Prediction": lambda: prediction_page.render(
                context=self.context,
            ),
            "Explainability": lambda: explainability_page.render(
                context=self.context,
                api_client=self.api_client,
            ),
            "Analytics": lambda: analytics_page.render(
                context=self.context,
                analytics=self.analytics,
            ),
            "Developer": lambda: developer_page.render(
                context=self.context,
            ),
            "Settings": lambda: settings_page.render(
                context=self.context,
            ),
        }

        route = routes.get(
            self.context.page
        )

        if route is None:
            st.error(
                f"Página não registrada: {self.context.page}"
            )
            return

        route()
