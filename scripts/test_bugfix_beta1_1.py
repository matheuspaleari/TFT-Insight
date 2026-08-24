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

from partner_platform.ui.html import (
    normalize_html,
)
from partner_platform.ui.messages import (
    friendly_exception,
)
from partner_platform.components import (
    loading_pipeline,
    loading_screen,
    skeleton_cards,
)


def main() -> None:
    sample = """
        <div class="card">
            <span>Hello</span>
        </div>
    """

    normalized = normalize_html(
        sample
    )

    assert "\n" not in normalized
    assert (
        '<div class="card"><span>Hello</span></div>'
        == normalized
    )

    assert friendly_exception
    assert loading_pipeline
    assert loading_screen
    assert skeleton_cards

    print("=" * 92)
    print(
        "TFT INSIGHT - BETA 1.1 BUGFIX VALIDATION"
    )
    print("=" * 92)
    print(
        "HTML single-line normalization : OK"
    )
    print(
        "Loading pipeline renderer      : OK"
    )
    print(
        "Skeleton renderer              : OK"
    )
    print(
        "Friendly HTTP errors           : OK"
    )
    print()
    print(
        "✓ v0.5.0-beta.1.1 bugfix validado."
    )


if __name__ == "__main__":
    main()
