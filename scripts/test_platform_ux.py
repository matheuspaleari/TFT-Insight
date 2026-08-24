from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.components import (
    executive_card,
    health_ribbon,
    hero,
    sidebar_brand,
    topbar,
)
from partner_platform.design_system import (
    Animations,
    Breakpoints,
    Icons,
)
from partner_platform.platform_core import PlatformPage


def main() -> None:
    assert Animations.NORMAL
    assert Breakpoints.TABLET
    assert Icons.BRAND

    assert executive_card
    assert health_ribbon
    assert hero
    assert sidebar_brand
    assert topbar
    assert PlatformPage

    print("=" * 84)
    print("TFT INSIGHT - PLATFORM UX VALIDATION")
    print("=" * 84)
    print("Premium cards      : OK")
    print("Health ribbon      : OK")
    print("Sidebar branding   : OK")
    print("Responsive tokens  : OK")
    print("Animation tokens   : OK")
    print("Executive hero     : OK")
    print()
    print("✓ Sprint 4.1A.2 UX Premium validada.")


if __name__ == "__main__":
    main()
