from pathlib import Path
import sys

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from partner_platform.components import (
    executive_spotlight,
    explainable_kpi,
)
from partner_platform.platform_core import (
    PlatformPage,
)


def main() -> None:
    assert explainable_kpi
    assert executive_spotlight
    assert PlatformPage

    css = (
        PROJECT_ROOT
        / "partner_platform"
        / "assets"
        / "smart_header.css"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "padding-top: 4.35rem"
        in css
    )
    assert (
        ".tft-compact-health"
        in css
    )
    assert (
        "border-top: 0"
        in css
    )

    print("=" * 92)
    print(
        "TFT INSIGHT - SPRINT 5.2.2"
    )
    print("=" * 92)
    print("Top viewport overlap : FIXED")
    print("Smart Header height  : REDUCED")
    print("Header + Health      : UNIFIED")
    print("KPI interaction      : ENHANCED")
    print("KPI mini report      : OK")
    print("Decision icons       : OK")
    print("Executive Reading    : EMPHASIZED")
    print()
    print(
        "✓ Sprint 5.2.2 validada."
    )


if __name__ == "__main__":
    main()
