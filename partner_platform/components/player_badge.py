import html

from partner_platform.ui import render_html


def player_badge(
    *,
    game_name: str,
    tag_line: str,
    region: str,
    match_count: int,
) -> None:
    render_html(
        f"""
        <div class="tft-player-badge">
            <div class="tft-player-badge-icon">👤</div>
            <div class="tft-player-badge-main">
                <div class="tft-player-badge-name">
                    {html.escape(game_name)}
                </div>
                <div class="tft-player-badge-meta">
                    #{html.escape(tag_line)} ·
                    {html.escape(region)} ·
                    {match_count} partidas
                </div>
            </div>
            <div class="tft-player-badge-state">
                ACTIVE
            </div>
        </div>
        """
    )
