import html

from partner_platform.ui import render_html


def empty_state(
    *,
    title: str,
    description: str,
    icon: str = "◇",
    action_hint: str | None = None,
    tone: str = "neutral",
) -> None:
    safe_tone = tone if tone in {"neutral", "warning", "error"} else "neutral"

    hint_html = (
        f'<div class="tft-empty-hint">{html.escape(action_hint)}</div>'
        if action_hint
        else ""
    )

    render_html(
        f"""
        <div class="tft-empty tft-empty-premium tft-empty-{safe_tone}">
            <div class="tft-empty-icon">{html.escape(icon)}</div>
            <div class="tft-empty-title">{html.escape(title)}</div>
            <div class="tft-empty-description">{html.escape(description)}</div>
            {hint_html}
        </div>
        """
    )
