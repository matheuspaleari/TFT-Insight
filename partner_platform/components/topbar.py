import html

from partner_platform.ui import render_html


def topbar(
    *,
    environment: str = "Development",
    api_version: str = "v1.0.0",
    contract_version: str = "v1.0.0",
    platform_version: str = "v0.5.0-beta.1",
) -> None:
    render_html(
        f"""
        <div class="tft-topbar">
            <div class="tft-topbar-left">
                <div class="tft-brand">
                    <span class="tft-brand-mark">◈</span>
                    <span>TFT Insight</span>
                </div>
                <span class="tft-chip">
                    Partner Platform {html.escape(platform_version)}
                </span>
            </div>

            <div class="tft-topbar-right">
                <span class="tft-chip">
                    ● {html.escape(environment)}
                </span>
                <span class="tft-topbar-meta">
                    API {html.escape(api_version)}
                </span>
                <span class="tft-topbar-meta">
                    Contract {html.escape(contract_version)}
                </span>
            </div>
        </div>
        """
    )
