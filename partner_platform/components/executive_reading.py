import html

from partner_platform.ui import render_html


def executive_reading(
    *,
    title: str,
    body: str,
) -> None:
    render_html(
        f"""
        <section class="tft-executive-reading">
            <div class="tft-executive-reading-icon">🧠</div>
            <div class="tft-executive-reading-content">
                <div class="tft-executive-reading-kicker">
                    LEITURA EXECUTIVA
                </div>
                <div class="tft-executive-reading-title">
                    {html.escape(title)}
                </div>
                <div class="tft-executive-reading-body">
                    {html.escape(body)}
                </div>
            </div>
        </section>
        """
    )
