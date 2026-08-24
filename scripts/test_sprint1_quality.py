from pathlib import Path
import sys
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.sprint1_engine import (
    AutoCalibrationEngine,
    FeatureImportanceEngine,
    KnowledgeRepository,
    PredictionCalibrationEngine,
    PredictionHistoryRecord,
)
from src.sprint1_engine.models import (
    AnalysisConfidence,
    SprintPredictionReport,
)


def main() -> None:
    with TemporaryDirectory() as directory:
        repository = KnowledgeRepository(
            Path(directory) / "quality_test.db"
        )
        repository.initialize()

        placements = [1, 2, 3, 4, 5, 6, 7, 8] * 4

        for index, placement in enumerate(placements, start=1):
            repository.save_prediction(
                PredictionHistoryRecord(
                    prediction_id=f"prediction-{index}",
                    match_id=f"match-{index}",
                    player_puuid="test-player",
                    source="player",
                    patch="16.15",
                    set_number=17,
                    top1_probability=15.0,
                    top4_probability=60.0,
                    bot4_probability=40.0,
                    expected_placement=4.0,
                    confidence=80.0,
                    model_version="1.1.0",
                )
            )
            repository.resolve_prediction(
                match_id=f"match-{index}",
                actual_placement=placement,
            )

        calibration = PredictionCalibrationEngine.evaluate(
            repository=repository,
            source="player",
            patch="16.15",
            set_number=17,
        )

        prediction = SprintPredictionReport(
            top1_probability=15.0,
            top4_probability=60.0,
            bot4_probability=40.0,
            expected_placement=4.0,
            risk="Médio",
            confidence=AnalysisConfidence(
                score=80.0,
                level="Alta",
                sample_size=32,
                evidence=("teste",),
                limitations=(),
            ),
        )

        calibrated = AutoCalibrationEngine.apply(
            prediction=prediction,
            calibration=calibration,
        )

        importance = FeatureImportanceEngine.explain_top4(
            historical_top4=55.0,
            challenger_top4=51.8,
            strategic_score=76.0,
            contest_score=53.0,
            flex_score=71.0,
            baseline_probability=50.0,
            final_probability=calibrated.top4_probability,
        )

        assert calibration.sample_size == 32
        assert len(importance.contributions) == 5
        assert abs(
            calibrated.top4_probability
            + calibrated.bot4_probability
            - 100.0
        ) < 0.01

        print("=" * 80)
        print("TFT INSIGHT - SPRINT 1.1 QUALITY VALIDATION")
        print("=" * 80)
        print(f"Previsões resolvidas : {calibration.sample_size}")
        print(f"Brier Score          : {calibration.brier_score:.4f}")
        print(f"Erro de calibração   : {calibration.calibration_error:.2f}%")
        print(f"Status               : {calibration.status}")
        print(f"Top 4 calibrado      : {calibrated.top4_probability:.2f}%")
        print("Feature importance   : OK")
        print("Prediction history   : OK")
        print("Auto calibration     : OK")
        print("SQLite migration     : OK")
        print()
        print("✓ Sprint 1 + correções de qualidade validadas.")


if __name__ == "__main__":
    main()
