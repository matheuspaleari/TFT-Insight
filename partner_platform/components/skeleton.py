from partner_platform.ui import render_html


def skeleton_cards(
    count: int = 4,
) -> None:
    blocks = "".join(
        """
        <div class="tft-skeleton-card">
            <div class="tft-skeleton-line tft-skeleton-small"></div>
            <div class="tft-skeleton-line tft-skeleton-large"></div>
            <div class="tft-skeleton-line tft-skeleton-medium"></div>
        </div>
        """
        for _ in range(
            max(1, count)
        )
    )

    render_html(
        '<div class="tft-skeleton-grid">'
        + blocks
        + "</div>"
    )
