from dataclasses import dataclass

from .augment_report import AugmentReport
from .economy_report import EconomyReport
from .itemization_report import ItemizationReport
from .positioning_report import PositioningReport
from .tempo_report import TempoReport


@dataclass(slots=True, frozen=True)
class StrategicReport:
    overall_score: float
    label: str

    economy: EconomyReport
    itemization: ItemizationReport
    tempo: TempoReport
    augment: AugmentReport
    positioning: PositioningReport

    strengths: tuple[str, ...]
    priorities: tuple[str, ...]
    summary: str
