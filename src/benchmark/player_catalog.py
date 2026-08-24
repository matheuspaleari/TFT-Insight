"""
Persistência do catálogo individual usado pelos benchmarks.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

@dataclass(slots=True, frozen=True)
class BenchmarkPlayerCatalogEntry:
    benchmark_id: str
    puuid: str
    game_name: str | None
    tag_line: str | None
    queue_type: str
    tier_at_collection: str
    division_at_collection: str
    league_points_at_collection: int
    current_tier: str
    current_division: str
    current_league_points: int
    matches_used: int
    metrics: dict[str, Any]
    collected_at: str
    rank_checked_at: str
    rank_history: tuple[dict[str, Any], ...] = ()

    @property
    def riot_id(self) -> str:
        if self.game_name and self.tag_line:
            return f"{self.game_name}#{self.tag_line}"
        return self.puuid

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rank_history"] = list(self.rank_history)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkPlayerCatalogEntry":
        return cls(
            benchmark_id=str(data["benchmark_id"]),
            puuid=str(data["puuid"]),
            game_name=data.get("game_name"),
            tag_line=data.get("tag_line"),
            queue_type=str(data.get("queue_type", "RANKED_TFT")),
            tier_at_collection=str(data["tier_at_collection"]),
            division_at_collection=str(data["division_at_collection"]),
            league_points_at_collection=int(data.get("league_points_at_collection", 0)),
            current_tier=str(data.get("current_tier", data["tier_at_collection"])),
            current_division=str(data.get("current_division", data["division_at_collection"])),
            current_league_points=int(data.get("current_league_points", data.get("league_points_at_collection", 0))),
            matches_used=int(data["matches_used"]),
            metrics=dict(data.get("metrics", {})),
            collected_at=str(data["collected_at"]),
            rank_checked_at=str(data.get("rank_checked_at", data["collected_at"])),
            rank_history=tuple(data.get("rank_history", [])),
        )

class BenchmarkPlayerCatalogRepository:
    DEFAULT_DIRECTORY = Path("data/benchmark")

    def __init__(self, directory: str | Path = DEFAULT_DIRECTORY) -> None:
        self.directory = Path(directory)

    def path_for(self, benchmark_id: str) -> Path:
        return self.directory / f"{benchmark_id.strip().lower()}_player_catalog.json"

    def save(self, *, benchmark_id: str, players: list[BenchmarkPlayerCatalogEntry]) -> Path:
        path = self.path_for(benchmark_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "benchmark_id": benchmark_id.strip().lower(),
            "generated_at": utc_now_iso(),
            "players_count": len(players),
            "players": [item.to_dict() for item in players],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, benchmark_id: str) -> list[BenchmarkPlayerCatalogEntry]:
        path = self.path_for(benchmark_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        players = data.get("players", [])
        if not isinstance(players, list):
            raise RuntimeError(f"Catálogo inválido: {path}")
        return [BenchmarkPlayerCatalogEntry.from_dict(item) for item in players if isinstance(item, dict)]

def metrics_to_dict(metrics: Any) -> dict[str, Any]:
    return asdict(metrics)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
