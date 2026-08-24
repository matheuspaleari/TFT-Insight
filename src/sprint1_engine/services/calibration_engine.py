from statistics import mean

from src.sprint1_engine.models import PredictionCalibrationReport
from src.sprint1_engine.repositories import KnowledgeRepository


class PredictionCalibrationEngine:
    """Mede se probabilidades previstas correspondem aos resultados reais."""

    MINIMUM_SAMPLE = 20

    @classmethod
    def evaluate(
        cls,
        *,
        repository: KnowledgeRepository,
        source: str = "player",
        patch: str | None = None,
        set_number: int | None = None,
    ) -> PredictionCalibrationReport:
        rows = repository.list_resolved_predictions(
            source=source,
            patch=patch,
            set_number=set_number,
        )

        if not rows:
            return PredictionCalibrationReport(
                sample_size=0,
                brier_score=1.0,
                mean_absolute_error=100.0,
                calibration_error=100.0,
                accuracy_score=0.0,
                optimism_bias=0.0,
                top4_calibration_offset=0.0,
                top1_calibration_offset=0.0,
                status="Sem dados",
                evidence=("Nenhuma previsão resolvida foi encontrada.",),
                limitations=(
                    "É necessário salvar previsões antes da partida e registrar a colocação real depois.",
                ),
            )

        top4_predictions = [float(row["top4_probability"]) / 100.0 for row in rows]
        top4_actual = [1.0 if int(row["actual_placement"]) <= 4 else 0.0 for row in rows]
        top1_predictions = [float(row["top1_probability"]) / 100.0 for row in rows]
        top1_actual = [1.0 if int(row["actual_placement"]) == 1 else 0.0 for row in rows]

        brier = mean(
            (prediction - actual) ** 2
            for prediction, actual in zip(top4_predictions, top4_actual)
        )
        mae = mean(
            abs(prediction - actual)
            for prediction, actual in zip(top4_predictions, top4_actual)
        )
        optimism = mean(top4_predictions) - mean(top4_actual)
        top4_offset = (mean(top4_actual) - mean(top4_predictions)) * 100.0
        top1_offset = (mean(top1_actual) - mean(top1_predictions)) * 100.0
        calibration_error = abs(optimism) * 100.0
        accuracy = max(0.0, 100.0 - brier * 100.0)

        sample = len(rows)
        status = (
            "Confiável" if sample >= 100 and calibration_error <= 5.0
            else "Em calibração" if sample >= cls.MINIMUM_SAMPLE
            else "Amostra pequena"
        )

        return PredictionCalibrationReport(
            sample_size=sample,
            brier_score=round(brier, 4),
            mean_absolute_error=round(mae * 100.0, 2),
            calibration_error=round(calibration_error, 2),
            accuracy_score=round(accuracy, 2),
            optimism_bias=round(optimism * 100.0, 2),
            top4_calibration_offset=round(top4_offset, 2),
            top1_calibration_offset=round(top1_offset, 2),
            status=status,
            evidence=(
                f"Previsões resolvidas: {sample}",
                f"Top 4 previsto médio: {mean(top4_predictions) * 100.0:.2f}%",
                f"Top 4 real: {mean(top4_actual) * 100.0:.2f}%",
            ),
            limitations=(
                "A calibração deve ser segmentada por patch e set quando houver amostra suficiente.",
                "Accuracy score é derivado do Brier Score e não representa acurácia de classificação simples.",
            ),
        )
