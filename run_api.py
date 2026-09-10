from __future__ import annotations

import os

import uvicorn


def _port() -> int:
    raw = os.getenv("PORT", "8000").strip()
    try:
        return int(raw)
    except ValueError:
        return 8000


if __name__ == "__main__":
    uvicorn.run(
        "src.integration_engine.api.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=_port(),
        reload=False,
    )
