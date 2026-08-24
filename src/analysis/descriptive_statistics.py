from pathlib import Path

import pandas as pd


class DescriptiveStatistics:
    """
    Calcula estatísticas descritivas para um dataset de métricas.
    """

    def analyze(
        self,
        dataset: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Retorna estatísticas descritivas das colunas numéricas.
        """

        if dataset.empty:
            raise ValueError("O dataset está vazio.")

        numeric_dataset = dataset.drop(columns=["player"])

        return numeric_dataset.describe().T

    def export_csv(
        self,
        statistics: pd.DataFrame,
        output_path: str | Path,
    ) -> Path:
        """
        Exporta as estatísticas para CSV.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        statistics.to_csv(path)

        return path