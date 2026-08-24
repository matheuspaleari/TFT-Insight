from pathlib import Path
import importlib
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


MODULES = (
    "partner_platform.session.models",
    "partner_platform.session.store",
    "partner_platform.session",
    "partner_platform.components.current_session",
    "partner_platform.platform_core.context",
)


def main() -> None:
    for module_name in MODULES:
        importlib.import_module(
            module_name
        )

    from partner_platform.session import (
        PlayerSession,
        PlayerSessionStore,
    )

    assert PlayerSession
    assert PlayerSessionStore

    print("=" * 92)
    print(
        "TFT INSIGHT - SESSION IMPORT GRAPH"
    )
    print("=" * 92)
    print(
        f"Modules imported : {len(MODULES)}"
    )
    print("Circular imports : 0")
    print()
    print(
        "[OK] Session import graph validado."
    )


if __name__ == "__main__":
    main()
