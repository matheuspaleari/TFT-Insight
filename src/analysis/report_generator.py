"""Geração do relatório consolidado da análise."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
try:
    from .feature_importance import FeatureImportanceResult
except ImportError:
    from feature_importance import FeatureImportanceResult

class ReportGenerator:
    def generate(self, *, dataset: pd.DataFrame, descriptive_statistics: pd.DataFrame, target_correlations: pd.Series, feature_importance: FeatureImportanceResult, target: str="average_placement") -> str:
        lines=[
            "="*64,"TFT INSIGHT — RELATÓRIO DE ANÁLISE","="*64,"",
            f"Jogadores analisados: {len(dataset)}",
            f"Partidas representadas: {int(dataset['matches_played'].sum()) if 'matches_played' in dataset.columns else 'não informado'}",
            f"Variável-alvo: {target}","",
            "AVALIAÇÃO DO MODELO","-"*64,
            f"Linhas de treino: {feature_importance.training_rows}",
            f"Linhas de teste: {feature_importance.test_rows}",
            f"MAE: {feature_importance.mae:.4f}",
            f"RMSE: {feature_importance.rmse:.4f}",
            f"R²: {feature_importance.r2:.4f}","",
            "CORRELAÇÃO COM A COLOCAÇÃO MÉDIA","-"*64,
            self._format_series(target_correlations),"",
            "IMPORTÂNCIA POR PERMUTAÇÃO","-"*64,
            self._format_percentage_series(feature_importance.permutation_importance),"",
            "IMPORTÂNCIA NATIVA DO RANDOM FOREST","-"*64,
            self._format_percentage_series(feature_importance.impurity_importance),"",
            "ESTATÍSTICAS DESCRITIVAS","-"*64,
            descriptive_statistics.round(4).to_string(),"",
            "OBSERVAÇÕES","-"*64,
            "average_gold_left permanece no estudo como curiosidade, mas não recebe peso automaticamente.",
            "top4_rate e bottom4_rate ficam fora do modelo padrão porque derivam diretamente da colocação e causariam vazamento de alvo.",
            "Os pesos finais só devem ser definidos após validar estabilidade em diferentes amostras.","",
        ]
        return "\n".join(lines)

    def save(self, report: str, output_path: str | Path) -> Path:
        path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(report,encoding="utf-8")
        return path

    @staticmethod
    def _format_series(series: pd.Series) -> str:
        return "\n".join(f"{name:<40} {value:>9.4f}" for name,value in series.items())

    @staticmethod
    def _format_percentage_series(series: pd.Series) -> str:
        return "\n".join(f"{name:<40} {value*100:>8.2f}%" for name,value in series.items())
