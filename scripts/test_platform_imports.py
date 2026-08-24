from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    from partner_platform.platform_core.page import PlatformPage
    from partner_platform.platform_core.application import PlatformApplication
    from partner_platform.platform_core.feature_registry import FeatureRegistry
    from partner_platform.pages import analytics_page

    assert PlatformPage
    assert PlatformApplication
    assert FeatureRegistry
    assert analytics_page

    print("=" * 90)
    print("TFT INSIGHT - IMPORT GRAPH VALIDATION")
    print("=" * 90)
    print("PlatformPage       : OK")
    print("PlatformApplication: OK")
    print("FeatureRegistry    : OK")
    print("Pages              : OK")
    print()
    print("[OK] Grafo de imports sem circularidade.")


if __name__ == "__main__":
    main()
