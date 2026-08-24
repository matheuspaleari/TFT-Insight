from dataclasses import dataclass, field

@dataclass(frozen=True)
class PostMatchInterpretationItem:
    signal_id: str
    title: str
    text: str
    importance: int
    internal_evidence_class: str
    personal_band: str | None = None

@dataclass(frozen=True)
class PostMatchInterpretation:
    headline: str
    overview: str
    focus_reading: str
    context_readings: tuple[PostMatchInterpretationItem, ...] = field(default_factory=tuple)
    missing_information: str = ""
    conclusion: str = ""
    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_evidence_class: bool = False
    counts_as_mission_evidence: bool = False
