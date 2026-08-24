from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from src.sprint1_engine.models import (
    PerformanceMeasurement,
    PredictionHistoryRecord,
)


class KnowledgeRepository:
    SCHEMA_VERSION = "1.1.0"

    def __init__(
        self,
        path: str | Path = "data/knowledge/tft_insight_knowledge.db",
    ) -> None:
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS processed_matches (
                    match_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    player_puuid TEXT NOT NULL,
                    patch TEXT NOT NULL DEFAULT '',
                    set_number INTEGER,
                    game_datetime INTEGER,
                    transformer_version TEXT NOT NULL,
                    learning_version TEXT NOT NULL,
                    placement INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    gold_left INTEGER NOT NULL,
                    last_round INTEGER NOT NULL,
                    players_eliminated INTEGER NOT NULL,
                    total_damage_to_players INTEGER NOT NULL,
                    PRIMARY KEY (match_id, source, player_puuid)
                );

                CREATE TABLE IF NOT EXISTS observations (
                    dimension TEXT NOT NULL,
                    observation_key TEXT NOT NULL,
                    source TEXT NOT NULL,
                    patch TEXT NOT NULL DEFAULT '',
                    set_number INTEGER,
                    uses INTEGER NOT NULL DEFAULT 0,
                    top4_count INTEGER NOT NULL DEFAULT 0,
                    win_count INTEGER NOT NULL DEFAULT 0,
                    placement_sum REAL NOT NULL DEFAULT 0,
                    level_sum REAL NOT NULL DEFAULT 0,
                    gold_sum REAL NOT NULL DEFAULT 0,
                    contest_sum REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (
                        dimension,
                        observation_key,
                        source,
                        patch,
                        set_number
                    )
                );

                CREATE INDEX IF NOT EXISTS idx_matches_source_patch
                ON processed_matches(source, patch, set_number);

                CREATE INDEX IF NOT EXISTS idx_observations_lookup
                ON observations(dimension, source, patch, set_number, uses);

                CREATE TABLE IF NOT EXISTS prediction_history (
                    prediction_id TEXT PRIMARY KEY,
                    match_id TEXT NOT NULL,
                    player_puuid TEXT NOT NULL,
                    source TEXT NOT NULL,
                    patch TEXT NOT NULL DEFAULT '',
                    set_number INTEGER,
                    top1_probability REAL NOT NULL,
                    top4_probability REAL NOT NULL,
                    bot4_probability REAL NOT NULL,
                    expected_placement REAL NOT NULL,
                    confidence REAL NOT NULL,
                    model_version TEXT NOT NULL,
                    actual_placement INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_prediction_match
                ON prediction_history(match_id, source, patch, set_number);

                CREATE INDEX IF NOT EXISTS idx_prediction_resolved
                ON prediction_history(source, actual_placement, patch, set_number);

                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    elapsed_ms REAL NOT NULL,
                    success INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_performance_operation
                ON performance_metrics(operation, created_at);

                CREATE TABLE IF NOT EXISTS calibration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    patch TEXT NOT NULL DEFAULT '',
                    set_number INTEGER,
                    sample_size INTEGER NOT NULL,
                    brier_score REAL NOT NULL,
                    calibration_error REAL NOT NULL,
                    top4_offset REAL NOT NULL,
                    top1_offset REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
                ("schema_version", self.SCHEMA_VERSION),
            )

    def is_processed(
        self,
        *,
        match_id: str,
        source: str,
        player_puuid: str,
        transformer_version: str,
        learning_version: str,
    ) -> bool:
        self.initialize()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT transformer_version, learning_version
                FROM processed_matches
                WHERE match_id = ? AND source = ? AND player_puuid = ?
                """,
                (match_id, source, player_puuid),
            ).fetchone()
        return bool(
            row
            and row["transformer_version"] == transformer_version
            and row["learning_version"] == learning_version
        )

    def save_match(
        self,
        *,
        values: dict[str, Any],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO processed_matches (
                    match_id, source, player_puuid, patch, set_number,
                    game_datetime, transformer_version, learning_version,
                    placement, level, gold_left, last_round,
                    players_eliminated, total_damage_to_players
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["match_id"], values["source"],
                    values["player_puuid"], values.get("patch", ""),
                    values.get("set_number"), values.get("game_datetime"),
                    values["transformer_version"], values["learning_version"],
                    values["placement"], values["level"], values["gold_left"],
                    values["last_round"], values["players_eliminated"],
                    values["total_damage_to_players"],
                ),
            )

    def upsert_observation(
        self,
        *,
        dimension: str,
        observation_key: str,
        source: str,
        patch: str,
        set_number: int | None,
        placement: int,
        level: int,
        gold_left: int,
        contest_score: float = 0.0,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO observations (
                    dimension, observation_key, source, patch, set_number,
                    uses, top4_count, win_count, placement_sum, level_sum,
                    gold_sum, contest_sum, payload_json
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    dimension, observation_key, source, patch, set_number
                ) DO UPDATE SET
                    uses = uses + 1,
                    top4_count = top4_count + excluded.top4_count,
                    win_count = win_count + excluded.win_count,
                    placement_sum = placement_sum + excluded.placement_sum,
                    level_sum = level_sum + excluded.level_sum,
                    gold_sum = gold_sum + excluded.gold_sum,
                    contest_sum = contest_sum + excluded.contest_sum,
                    payload_json = excluded.payload_json
                """,
                (
                    dimension, observation_key, source, patch, set_number,
                    int(placement <= 4), int(placement == 1), float(placement),
                    float(level), float(gold_left), float(contest_score),
                    json.dumps(payload or {}, ensure_ascii=False),
                ),
            )

    def get_observation(
        self,
        *,
        dimension: str,
        observation_key: str,
        source: str,
        patch: str = "",
        set_number: int | None = None,
    ) -> dict[str, Any] | None:
        self.initialize()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM observations
                WHERE dimension = ? AND observation_key = ?
                  AND source = ? AND patch = ? AND set_number IS ?
                """,
                (dimension, observation_key, source, patch, set_number),
            ).fetchone()
        return dict(row) if row else None

    def aggregate_source(
        self,
        *,
        source: str,
        patch: str | None = None,
        set_number: int | None = None,
    ) -> dict[str, float]:
        self.initialize()
        query = "SELECT * FROM processed_matches WHERE source = ?"
        params: list[Any] = [source]
        if patch is not None:
            query += " AND patch LIKE ?"
            params.append(f"{patch}%")
        if set_number is not None:
            query += " AND set_number = ?"
            params.append(set_number)
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        if not rows:
            return {}
        total = len(rows)
        return {
            "sample_size": float(total),
            "top4_rate": sum(r["placement"] <= 4 for r in rows) / total * 100,
            "win_rate": sum(r["placement"] == 1 for r in rows) / total * 100,
            "average_placement": sum(r["placement"] for r in rows) / total,
            "average_level": sum(r["level"] for r in rows) / total,
            "level_8_rate": sum(r["level"] >= 8 for r in rows) / total * 100,
            "level_9_rate": sum(r["level"] >= 9 for r in rows) / total * 100,
            "average_gold_left": sum(r["gold_left"] for r in rows) / total,
            "average_damage": (
                sum(r["total_damage_to_players"] for r in rows) / total
            ),
        }

    def save_prediction(
        self,
        record: PredictionHistoryRecord,
    ) -> None:
        self.initialize()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO prediction_history (
                    prediction_id, match_id, player_puuid, source, patch,
                    set_number, top1_probability, top4_probability,
                    bot4_probability, expected_placement, confidence,
                    model_version, actual_placement
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.prediction_id, record.match_id, record.player_puuid,
                    record.source, record.patch, record.set_number,
                    record.top1_probability, record.top4_probability,
                    record.bot4_probability, record.expected_placement,
                    record.confidence, record.model_version,
                    record.actual_placement,
                ),
            )

    def resolve_prediction(
        self,
        *,
        match_id: str,
        actual_placement: int,
    ) -> int:
        if not 1 <= actual_placement <= 8:
            raise ValueError("actual_placement deve estar entre 1 e 8.")
        self.initialize()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE prediction_history
                SET actual_placement = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE match_id = ? AND actual_placement IS NULL
                """,
                (actual_placement, match_id),
            )
            return cursor.rowcount

    def list_resolved_predictions(
        self,
        *,
        source: str,
        patch: str | None = None,
        set_number: int | None = None,
    ) -> list[dict[str, Any]]:
        self.initialize()
        query = (
            "SELECT * FROM prediction_history "
            "WHERE source = ? AND actual_placement IS NOT NULL"
        )
        params: list[Any] = [source]
        if patch is not None:
            query += " AND patch LIKE ?"
            params.append(f"{patch}%")
        if set_number is not None:
            query += " AND set_number = ?"
            params.append(set_number)
        query += " ORDER BY created_at DESC"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def save_performance_measurement(
        self,
        measurement: PerformanceMeasurement,
    ) -> None:
        self.initialize()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO performance_metrics (
                    operation, elapsed_ms, success, metadata_json
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    measurement.operation,
                    measurement.elapsed_ms,
                    int(measurement.success),
                    json.dumps(measurement.metadata, ensure_ascii=False),
                ),
            )

    def performance_summary(self) -> list[dict[str, Any]]:
        self.initialize()
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT operation, COUNT(*) AS executions,
                       AVG(elapsed_ms) AS average_ms,
                       MAX(elapsed_ms) AS maximum_ms,
                       AVG(success) * 100.0 AS success_rate
                FROM performance_metrics
                GROUP BY operation
                ORDER BY average_ms DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]
