import html

from partner_platform.ui import render_html


def decision_step(
    *,
    label: str,
    value: str,
    state: str = "neutral",
    last: bool = False,
) -> None:
    state_class = {
        "positive": "tft-decision-positive",
        "warning": "tft-decision-warning",
        "negative": "tft-decision-negative",
        "neutral": "tft-decision-neutral",
    }.get(
        state,
        "tft-decision-neutral",
    )

    connector = (
        ""
        if last
        else '<div class="tft-decision-connector">↓</div>'
    )

    render_html(
        f"""
        <div class="tft-decision-step {state_class}">
            <div class="tft-decision-label">
                {html.escape(label)}
            </div>
            <div class="tft-decision-value">
                {html.escape(value)}
            </div>
        </div>
        {connector}
        """
    )
