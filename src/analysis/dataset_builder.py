"""Construção do dataset de análise a partir de PlayerMetrics."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True, slots=True)
class PlayerMetricsRecord:
    """Associa um identificador de jogador ao seu PlayerMetrics."""

    player: str
    metrics: Any


class DatasetBuilder:
    """Transforma métricas agregadas por jogador em um DataFrame."""

    COLUMNS = [
        "player",
        "matches_played",
        "average_placement",
        "top4_rate",
        "win_rate",
        "average_level",
        "placement_standard_deviation",
        "bottom4_rate",
        "best_placement",
        "worst_placement",
        "average_damage_to_players",
        "average_players_eliminated",
        "average_gold_left",
    ]

    def build(
        self,
        players_metrics: Iterable[PlayerMetricsRecord | tuple[str, Any]],
    ) -> pd.DataFrame:
        """Cria uma linha no DataFrame para cada jogador."""

        rows: list[dict[str, Any]] = []

        for item in players_metrics:
            record = self._normalize_record(item)
            rows.append(self._to_row(record))

        if not rows:
            raise ValueError("Nenhuma métrica de jogador foi fornecida.")

        dataset = pd.DataFrame(rows, columns=self.COLUMNS)

        self._validate(dataset)

        return dataset

    def export_csv(
        self,
        dataset: pd.DataFrame,
        output_path: str | Path,
    ) -> Path:
        """Salva o dataset em CSV e retorna o caminho do arquivo."""

        self._validate(dataset)

        path = Path(output_path)

        # Cria automaticamente pastas que ainda não existem.
        path.parent.mkdir(parents=True, exist_ok=True)

        dataset.to_csv(
            path,
            index=False,
            encoding="utf-8",
        )

        return path

    @staticmethod
    def _normalize_record(
        item: PlayerMetricsRecord | tuple[str, Any],
    ) -> PlayerMetricsRecord:
        if isinstance(item, PlayerMetricsRecord):
            return item

        if isinstance(item, tuple) and len(item) == 2:
            player, metrics = item

            return PlayerMetricsRecord(
                player=str(player),
                metrics=metrics,
            )

        raise TypeError(
            "Cada item deve ser PlayerMetricsRecord ou uma tupla "
            "('player', PlayerMetrics)."
        )

    @staticmethod
    def _to_row(record: PlayerMetricsRecord) -> dict[str, Any]:
        metrics = record.metrics

        try:
            return {
                "player": record.player,
                "matches_played": metrics.general.matches_played,
                "average_placement": metrics.general.average_placement,
                "top4_rate": metrics.general.top4_rate,
                "win_rate": metrics.general.win_rate,
                "average_level": metrics.general.average_level,
                "placement_standard_deviation": (
                    metrics.consistency.placement_standard_deviation
                ),
                "bottom4_rate": metrics.consistency.bottom4_rate,
                "best_placement": metrics.consistency.best_placement,
                "worst_placement": metrics.consistency.worst_placement,
                "average_damage_to_players": (
                    metrics.combat.average_damage_to_players
                ),
                "average_players_eliminated": (
                    metrics.combat.average_players_eliminated
                ),
                "average_gold_left": metrics.economy.average_gold_left,
            }

        except AttributeError as error:
            raise TypeError(
                f"As métricas do jogador '{record.player}' "
                "não seguem a estrutura esperada de PlayerMetrics."
            ) from error

    @staticmethod
    def _validate(dataset: pd.DataFrame) -> None:
        if dataset.empty:
            raise ValueError("O dataset está vazio.")

        numeric_columns = dataset.drop(columns=["player"])

        if numeric_columns.isna().any().any():
            columns_with_missing_values = numeric_columns.columns[
                numeric_columns.isna().any()
            ].tolist()

            raise ValueError(
                "O dataset contém valores ausentes nas colunas: "
                f"{columns_with_missing_values}"
            )

        if dataset["player"].duplicated().any():
            duplicated_players = dataset.loc[
                dataset["player"].duplicated(),
                "player",
            ].tolist()

            raise ValueError(
                f"Existem jogadores duplicados: {duplicated_players}"
            )