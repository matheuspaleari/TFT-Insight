import json
from pathlib import Path
from typing import Any


class StaticDataRepository:
    def __init__(
        self,
        base_directory: str | Path = "data/static_data",
    ) -> None:
        self.base_directory = Path(base_directory)

    def save(
        self,
        *,
        version: str,
        locale: str,
        filename: str,
        data: dict[str, Any],
    ) -> Path:
        path = (
            self.base_directory
            / version
            / locale
            / filename
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load(
        self,
        *,
        version: str,
        locale: str,
        filename: str,
    ) -> dict[str, Any]:
        path = (
            self.base_directory
            / version
            / locale
            / filename
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def has_complete_version(
        self,
        *,
        version: str,
        locale: str,
    ) -> bool:
        return all(
            (
                self.base_directory
                / version
                / locale
                / filename
            ).exists()
            for filename in (
                "tft-champion.json",
                "tft-item.json",
                "tft-trait.json",
            )
        )

    def list_cached_versions(self, locale: str) -> list[str]:
        if not self.base_directory.exists():
            return []
        versions = [
            path.name
            for path in self.base_directory.iterdir()
            if path.is_dir() and (path / locale).is_dir()
        ]
        return sorted(versions, reverse=True)
