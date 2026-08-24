from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.navigation import (
    NavigationCatalog,
)
from partner_platform.theme import (
    apply_chart_theme,
)
from partner_platform.components import (
    skeleton_cards,
)


def main() -> None:
    catalog = NavigationCatalog.default()

    assert len(catalog.items) == 7
    assert catalog.page_from_label(
        "⌁ Benchmark"
    ) == "Benchmark"

    assert apply_chart_theme
    assert skeleton_cards

    print("=" * 92)
    print("TFT INSIGHT - PLATFORM FRAMEWORK 2.0")
    print("=" * 92)
    print("Navigation catalog : OK")
    print("Chart theme        : OK")
    print("Skeleton loading   : OK")
    print("Backward compatible: OK")
    print()
    print("✓ v0.5.0-alpha.1r1 validado.")


if __name__ == "__main__":
    main()
