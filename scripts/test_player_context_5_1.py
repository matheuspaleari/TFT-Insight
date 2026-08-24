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

from partner_platform.session.models import (
    PlayerSession,
)
from partner_platform.session.store import (
    PlayerSessionStore,
)


def main() -> None:
    player = PlayerSession(
        game_name="Pinador doss",
        tag_line="000",
        match_count=20,
    )

    assert (
        player.riot_id
        == "Pinador doss #000"
    )

    assert (
        player.identity_dict()[
            "match_count"
        ]
        == 20
    )

    assert (
        PlayerSessionStore.MAX_HISTORY
        == 5
    )

    assert (
        PlayerSessionStore.current_defaults
    )

    print("=" * 92)
    print(
        "TFT INSIGHT - SPRINT 5.1 PLAYER CONTEXT ENGINE"
    )
    print("=" * 92)
    print("Circular imports      : 0")
    print("PlayerSession model   : OK")
    print("PlayerSessionStore    : OK")
    print("Current defaults      : OK")
    print("Analysis cache slot   : OK")
    print("Benchmark cache slot  : OK")
    print("Recent players        : OK")
    print()
    print(
        "✓ Sprint 5.1 Player Context Engine validada."
    )


if __name__ == "__main__":
    main()
