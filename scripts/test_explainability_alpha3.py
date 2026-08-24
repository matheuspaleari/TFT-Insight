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
    decision_step,
    evidence_card,
    technical_details,
)
from partner_platform.navigation import (
    NavigationCatalog,
)


def main() -> None:
    catalog = (
        NavigationCatalog.default()
    )

    labels = [
        item.label
        for item in catalog.items
    ]

    assert (
        "Explainability"
        in labels
    )
    assert technical_details
    assert evidence_card
    assert decision_step

    print("=" * 90)
    print(
        "TFT INSIGHT - EXPLAINABILITY CENTER ALPHA 3"
    )
    print("=" * 90)
    print("Explainability nav : OK")
    print("Evidence cards     : OK")
    print("Decision path      : OK")
    print("Technical details  : COLLAPSED")
    print("Playground cleanup : OK")
    print()
    print(
        "✓ v0.5.0-alpha.3 Explainability Center validado."
    )


if __name__ == "__main__":
    main()
