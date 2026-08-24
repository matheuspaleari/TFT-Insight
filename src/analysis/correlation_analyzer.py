from pathlib import Path

import pandas as pd


class CorrelationAnalyzer:
    """
    Analisa a correlação entre as métricas numéricas
    e uma variável-alvo.
    """

    def analyze(
        self,
        dataset: pd.DataFrame,
        target: str = "average_placement",
    ) -> pd.DataFrame:
        """
        Calcula a correlação de Pearson das métricas
        com a variável-alvo.
        """

        if dataset.empty:
            raise ValueError("O dataset está vazio.")

        if target not in dataset.columns:
            raise ValueError(
                f"A coluna-alvo '{target}' não existe no dataset."
            )

        numeric_dataset = dataset.select_dtypes(
            include="number"
        )

        if target not in numeric_dataset.columns:
            raise ValueError(
                f"A coluna-alvo '{target}' não é numérica."
            )

        correlations = numeric_dataset.corr(
            method="pearson"
        )[target]

        correlations = correlations.drop(
            labels=[target]
        )

        # Remove colunas constantes, cuja correlação resulta em NaN.
        correlations = correlations.dropna()

        result = correlations.reset_index()

        result.columns = [
            "metric",
            "correlation",
        ]

        result["absolute_correlation"] = (
            result["correlation"].abs()
        )

        result = result.sort_values(
            by="absolute_correlation",
            ascending=False,
        )

        return result.reset_index(drop=True)

    def export_csv(
        self,
        correlations: pd.DataFrame,
        output_path: str | Path,
    ) -> Path:
        """
        Exporta o resultado das correlações para CSV.
        """

        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        correlations.to_csv(
            path,
            index=False,
        )

        return path