import json
from pathlib import Path
from typing import Any


class RichItemRepository:
    def __init__(
        self,
        path: str | Path = (
            "data/static_data/communitydragon/"
            "latest/pt_br.json"
        ),
    ) -> None:
        self.path = Path(path)

    def save(self, data: dict[str, Any]) -> Path:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return self.path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(self.path)

        data = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "Cache do CommunityDragon inválido."
            )

        return data

    def exists(self) -> bool:
        return self.path.exists()
