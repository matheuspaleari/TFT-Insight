from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split


@dataclass(slots=True, frozen=True)
class FeatureImportanceResult:
    """
    Resultado completo da análise de importância das métricas.
    """

    importances: pd.DataFrame
    mae: float
    rmse: float
    r2: float
    training_samples: int
    test_samples: int


class FeatureImportanceAnalyzer:
    """
    Analisa quais métricas têm maior influência sobre
    a colocação média dos jogadores.
    """

    DEFAULT_FEATURES = [
        "average_damage_to_players",
        "average_players_eliminated",
        "average_level",
        "placement_standard_deviation",
    ]

    def __init__(
        self,
        n_estimators: int = 500,
        random_state: int = 42,
        test_size: float = 0.30,
    ) -> None:
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.test_size = test_size

    def analyze(
        self,
        dataset: pd.DataFrame,
        target: str = "average_placement",
        features: list[str] | None = None,
    ) -> FeatureImportanceResult:
        """
        Treina uma Random Forest e calcula:

        - importância interna da Random Forest;
        - importância por permutação;
        - MAE;
        - RMSE;
        - R².
        """

        if dataset.empty:
            raise ValueError("O dataset está vazio.")

        selected_features = features or self.DEFAULT_FEATURES

        self._validate_columns(
            dataset=dataset,
            target=target,
            features=selected_features,
        )

        analysis_dataset = dataset[
            selected_features + [target]
        ].dropna()

        if len(analysis_dataset) < 5:
            raise ValueError(
                "São necessárias pelo menos 5 linhas válidas "
                "para executar a análise."
            )

        x = analysis_dataset[selected_features]
        y = analysis_dataset[target]

        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
        )

        model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )

        model.fit(x_train, y_train)

        predictions = model.predict(x_test)

        mae = mean_absolute_error(
            y_test,
            predictions,
        )

        rmse = mean_squared_error(
            y_test,
            predictions,
        ) ** 0.5

        # O R² não é confiável com somente uma amostra de teste.
        if len(y_test) >= 2:
            r2 = r2_score(
                y_test,
                predictions,
            )
        else:
            r2 = float("nan")

        permutation = permutation_importance(
            estimator=model,
            X=x_test,
            y=y_test,
            n_repeats=30,
            random_state=self.random_state,
            n_jobs=-1,
            scoring="neg_mean_absolute_error",
        )

        importances = pd.DataFrame(
            {
                "metric": selected_features,
                "random_forest_importance": (
                    model.feature_importances_
                ),
                "permutation_importance": (
                    permutation.importances_mean
                ),
                "permutation_std": (
                    permutation.importances_std
                ),
            }
        )

        importances["normalized_importance"] = (
            self._normalize_importance(
                importances["permutation_importance"]
            )
        )

        importances = importances.sort_values(
            by="normalized_importance",
            ascending=False,
        ).reset_index(drop=True)

        return FeatureImportanceResult(
            importances=importances,
            mae=float(mae),
            rmse=float(rmse),
            r2=float(r2),
            training_samples=len(x_train),
            test_samples=len(x_test),
        )

    def export_importances(
        self,
        result: FeatureImportanceResult,
        output_path: str | Path,
    ) -> Path:
        """
        Exporta as importâncias das métricas para CSV.
        """

        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        result.importances.to_csv(
            path,
            index=False,
        )

        return path

    def export_metrics(
        self,
        result: FeatureImportanceResult,
        output_path: str | Path,
    ) -> Path:
        """
        Exporta as métricas de avaliação do modelo para CSV.
        """

        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        metrics = pd.DataFrame(
            [
                {
                    "mae": result.mae,
                    "rmse": result.rmse,
                    "r2": result.r2,
                    "training_samples": (
                        result.training_samples
                    ),
                    "test_samples": result.test_samples,
                }
            ]
        )

        metrics.to_csv(
            path,
            index=False,
        )

        return path

    @staticmethod
    def _validate_columns(
        dataset: pd.DataFrame,
        target: str,
        features: list[str],
    ) -> None:
        required_columns = features + [target]

        missing_columns = [
            column
            for column in required_columns
            if column not in dataset.columns
        ]

        if missing_columns:
            raise ValueError(
                "As seguintes colunas não existem no dataset: "
                f"{missing_columns}"
            )

        non_numeric_columns = [
            column
            for column in required_columns
            if not pd.api.types.is_numeric_dtype(
                dataset[column]
            )
        ]

        if non_numeric_columns:
            raise ValueError(
                "As seguintes colunas precisam ser numéricas: "
                f"{non_numeric_columns}"
            )

    @staticmethod
    def _normalize_importance(
        importances: pd.Series,
    ) -> pd.Series:
        """
        Transforma as importâncias positivas em pesos cuja soma é 1.

        Importâncias negativas são convertidas para zero.
        """

        positive_importances = importances.clip(
            lower=0
        )

        total = positive_importances.sum()

        if total == 0:
            return pd.Series(
                [0.0] * len(importances),
                index=importances.index,
            )

        return positive_importances / total