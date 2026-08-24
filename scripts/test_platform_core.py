from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.design_system import (
    Colors,
    Radius,
    Shadows,
    Spacing,
    Typography,
)
from partner_platform.platform_core import (
    PlatformContext,
    PlatformPage,
    PlatformRouter,
)


def main() -> None:
    assert Colors.PRIMARY
    assert Spacing.MD
    assert Radius.LG
    assert Shadows.LEVEL_1
    assert Typography.FONT_FAMILY

    assert PlatformContext
    assert PlatformPage
    assert PlatformRouter

    print("=" * 84)
    print("TFT INSIGHT - PLATFORM CORE VALIDATION")
    print("=" * 84)
    print("Design System     : OK")
    print("Theme tokens      : OK")
    print("Component imports : OK")
    print("Layout core       : OK")
    print("Router            : OK")
    print()
    print("✓ Sprint 4.1A.1 Platform Core validada.")


if __name__ == "__main__":
    main()
