import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.integration_engine.api import app


OUTPUT = (
    PROJECT_ROOT
    / "docs"
    / "openapi"
    / "tft_insight_api_v1.json"
)


def main() -> None:
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            app.openapi(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"OpenAPI exportado para: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
