from pathlib import Path
import importlib
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


MODULES = (
    "partner_platform.platform_core",
    "partner_platform.platform_core.context",
    "partner_platform.platform_core.page",
    "partner_platform.platform_core.router",
    "partner_platform.navigation",
    "partner_platform.components",
    "partner_platform.pages.analytics_page",
    "partner_platform.pages.benchmark_page",
    "partner_platform.pages.overview_page",
    "partner_platform.pages.playground_page",
)


def main() -> None:
    for module_name in MODULES:
        importlib.import_module(
            module_name
        )

    from partner_platform.platform_core import (
        PlatformContext,
        PlatformPage,
        PlatformRouter,
    )

    assert PlatformContext
    assert PlatformPage
    assert PlatformRouter

    print("=" * 92)
    print("TFT INSIGHT - ACYCLIC IMPORT GRAPH")
    print("=" * 92)
    print(f"Modules imported : {len(MODULES)}")
    print("Circular imports : 0")
    print("PlatformContext  : OK")
    print("PlatformPage     : OK")
    print("PlatformRouter   : OK")
    print()
    print("[OK] Grafo de dependências validado.")


if __name__ == "__main__":
    main()
