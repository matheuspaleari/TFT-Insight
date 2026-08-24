from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class HistoricalFilter:
    limit: int | None = None
    patch: str | None = None
    set_number: int | None = None


class HistoricalMatchRepository:
    def __init__(
        self,
        path: str | Path = "data/history/matches.jsonl",
    ) -> None:
        self.path = Path(path)

    def save_raw_match(
        self,
        *,
        match_id: str,
        puuid: str,
        payload: dict[str, Any],
    ) -> bool:
        if self.contains(match_id):
            return False

        info = payload.get("info", {})

        record = {
            "match_id": match_id,
            "puuid": puuid,
            "patch": str(info.get("game_version", "")),
            "set_number": info.get("tft_set_number"),
            "game_datetime": info.get("game_datetime"),
            "payload": payload,
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("a", encoding="utf-8") as output:
            output.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

        return True

    def contains(self, match_id: str) -> bool:
        if not self.path.exists():
            return False

        with self.path.open("r", encoding="utf-8") as source:
            for line in source:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("match_id") == match_id:
                    return True

        return False

    def load(
        self,
        *,
        puuid: str | None = None,
        historical_filter: HistoricalFilter | None = None,
    ) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        filter_value = historical_filter or HistoricalFilter()
        records = []

        with self.path.open("r", encoding="utf-8") as source:
            for line in source:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if puuid and record.get("puuid") != puuid:
                    continue

                if (
                    filter_value.patch
                    and not str(record.get("patch", "")).startswith(
                        filter_value.patch
                    )
                ):
                    continue

                if (
                    filter_value.set_number is not None
                    and record.get("set_number")
                    != filter_value.set_number
                ):
                    continue

                records.append(record)

        records.sort(
            key=lambda item: item.get("game_datetime") or 0,
            reverse=True,
        )

        if filter_value.limit is not None:
            records = records[:filter_value.limit]

        return records
