import html

from partner_platform.ui import render_html


def loading_pipeline(
    steps: list[tuple[str, int, str]],
) -> None:
    rows = []

    for label, percent, status in steps:
        safe_percent = max(
            0,
            min(percent, 100),
        )

        rows.append(
            f"""
            <div class="tft-pipeline-row">
                <div class="tft-pipeline-label">
                    {html.escape(label)}
                </div>
                <div class="tft-pipeline-bar">
                    <div
                        class="tft-pipeline-fill"
                        style="width:{safe_percent}%"
                    ></div>
                </div>
                <div class="tft-pipeline-state">
                    {html.escape(status)}
                </div>
            </div>
            """
        )

    render_html(
        '<div class="tft-pipeline">'
        + "".join(rows)
        + "</div>"
    )
