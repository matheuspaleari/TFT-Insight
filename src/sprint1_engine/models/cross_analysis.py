from dataclasses import dataclass, field

from .confidence import AnalysisConfidence


@dataclass(slots=True, frozen=True)
class CrossAnalysisReport:
    score: float
    label: str
    confidence: AnalysisConfidence
    interactions: tuple[str, ...] = field(default_factory=tuple)
    priorities: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
