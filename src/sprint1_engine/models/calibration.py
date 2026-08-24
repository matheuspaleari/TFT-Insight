from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class FeatureContribution:
    feature: str
    value: float
    contribution: float
    direction: str
    explanation: str


@dataclass(slots=True, frozen=True)
class FeatureImportanceReport:
    baseline_probability: float
    final_probability: float
    contributions: tuple[FeatureContribution, ...] = field(
        default_factory=tuple
    )


@dataclass(slots=True, frozen=True)
class PredictionCalibrationReport:
    sample_size: int
    brier_score: float
    mean_absolute_error: float
    calibration_error: float
    accuracy_score: float
    optimism_bias: float
    top4_calibration_offset: float
    top1_calibration_offset: float
    status: str
    evidence: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class PerformanceMeasurement:
    operation: str
    elapsed_ms: float
    success: bool
    metadata: tuple[str, ...] = field(default_factory=tuple)
