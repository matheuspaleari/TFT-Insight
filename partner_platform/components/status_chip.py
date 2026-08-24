import html

from partner_platform.ui import render_html


def status_chip(
    label: str,
    *,
    status: str = "online",
) -> None:
    symbol = {
        "online": "●",
        "warning": "●",
        "offline": "●",
        "info": "●",
    }.get(
        status,
        "●",
    )

    render_html(
        f"""
        <span class="tft-chip">
            {symbol} {html.escape(label)}
        </span>
        """
    )
