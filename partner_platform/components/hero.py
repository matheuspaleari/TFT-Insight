import html

from partner_platform.ui import render_html


def hero(
    *,
    title: str,
    subtitle: str,
    eyebrow: str = "TFT INSIGHT PARTNER PLATFORM",
    badges: tuple[str, ...] = (),
) -> None:
    badge_html = "".join(
        f'<span class="tft-chip">{html.escape(item)}</span>'
        for item in badges
    )

    render_html(
        f"""
        <section class="tft-hero">
            <div class="tft-eyebrow">
                {html.escape(eyebrow)}
            </div>
            <div class="tft-title">
                {html.escape(title)}
            </div>
            <div class="tft-subtitle">
                {html.escape(subtitle)}
            </div>
            <div class="tft-hero-badges">
                {badge_html}
            </div>
        </section>
        """
    )
