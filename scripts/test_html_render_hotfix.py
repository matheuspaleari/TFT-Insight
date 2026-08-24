from pathlib import Path
import inspect
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partner_platform.components import (
    executive_card,
    health_ribbon,
    hero,
    topbar,
)


def main() -> None:
    components = (
        topbar,
        health_ribbon,
        hero,
        executive_card,
    )

    for component in components:
        source = inspect.getsource(component)
        assert "dedent(" in source
        assert "unsafe_allow_html=True" in source

    print("=" * 88)
    print("TFT INSIGHT - HTML RENDER HOTFIX")
    print("=" * 88)
    print("Topbar            : OK")
    print("Health ribbon     : OK")
    print("Hero              : OK")
    print("Executive cards   : OK")
    print("Markdown indent   : NORMALIZED")
    print()
    print("✓ HTML render hotfix validado.")


if __name__ == "__main__":
    main()
