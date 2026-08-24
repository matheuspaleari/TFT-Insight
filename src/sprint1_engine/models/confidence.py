from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class AnalysisConfidence:
    score: float
    level: str
    sample_size: int
    evidence: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score deve estar entre 0 e 100.")
        if self.sample_size < 0:
            raise ValueError("sample_size não pode ser negativo.")
