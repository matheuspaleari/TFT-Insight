from dataclasses import dataclass, field

from .confidence import AnalysisConfidence


@dataclass(slots=True, frozen=True)
class PregameGuidanceReport:
    pivot_attention: str
    win_condition: str
    confidence: AnalysisConfidence
    evidence: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
