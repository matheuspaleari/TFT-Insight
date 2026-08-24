"""Executa as etapas 1 a 3 da análise usando um dataset CSV."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
try:
    from .correlation_analyzer import CorrelationAnalyzer
    from .descriptive_statistics import DescriptiveStatistics
    from .feature_importance import FeatureImportanceAnalyzer
    from .report_generator import ReportGenerator
except ImportError:
    from correlation_analyzer import CorrelationAnalyzer
    from descriptive_statistics import DescriptiveStatistics
    from feature_importance import FeatureImportanceAnalyzer
    from report_generator import ReportGenerator

def run_analysis(dataset_path: str | Path, output_path: str | Path="analysis_report.txt") -> str:
    dataset=pd.read_csv(dataset_path)
    descriptive=DescriptiveStatistics().analyze(dataset)
    correlations=CorrelationAnalyzer().with_target(dataset)
    importance=FeatureImportanceAnalyzer().analyze(dataset)
    generator=ReportGenerator()
    report=generator.generate(dataset=dataset,descriptive_statistics=descriptive,target_correlations=correlations,feature_importance=importance)
    generator.save(report,output_path)
    return report

def parse_args():
    parser=argparse.ArgumentParser(description="Executa a análise estatística do TFT Insight.")
    parser.add_argument("dataset",help="Caminho do CSV gerado a partir dos PlayerMetrics.")
    parser.add_argument("--output",default="analysis_report.txt",help="Caminho do relatório de saída.")
    return parser.parse_args()

if __name__=="__main__":
    args=parse_args(); print(run_analysis(args.dataset,args.output))
