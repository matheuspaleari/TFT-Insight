from dataclasses import replace

from src.sprint1_engine.models import (
    PredictionCalibrationReport,
    SprintPredictionReport,
)


class AutoCalibrationEngine:
    MAX_ADJUSTMENT = 12.0

    @classmethod
    def apply(
        cls,
        *,
        prediction: SprintPredictionReport,
        calibration: PredictionCalibrationReport,
    ) -> SprintPredictionReport:
        if calibration.sample_size < 20:
            return prediction

        top4_adjustment = max(
            -cls.MAX_ADJUSTMENT,
            min(cls.MAX_ADJUSTMENT, calibration.top4_calibration_offset),
        )
        top1_adjustment = max(
            -cls.MAX_ADJUSTMENT,
            min(cls.MAX_ADJUSTMENT, calibration.top1_calibration_offset),
        )

        top4 = max(0.0, min(100.0, prediction.top4_probability + top4_adjustment))
        top1 = max(0.0, min(top4, prediction.top1_probability + top1_adjustment))
        bot4 = 100.0 - top4

        return replace(
            prediction,
            top1_probability=round(top1, 2),
            top4_probability=round(top4, 2),
            bot4_probability=round(bot4, 2),
            evidence=(
                *prediction.evidence,
                f"Auto calibration Top 4: {top4_adjustment:+.2f} pontos",
                f"Auto calibration Top 1: {top1_adjustment:+.2f} pontos",
            ),
            limitations=(
                *prediction.limitations,
                "A auto calibração é limitada a 12 pontos para evitar correções instáveis.",
            ),
        )
