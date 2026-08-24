from dataclasses import dataclass, field

from .unit_role_seed import UnitRoleSeed


@dataclass(slots=True, frozen=True)
class RoleSeedAssessment:
    role: UnitRoleSeed
    confidence: float

    offense_score: float
    defense_score: float
    utility_score: float

    evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name, value in (
            ("confidence", self.confidence),
            ("offense_score", self.offense_score),
            ("defense_score", self.defense_score),
            ("utility_score", self.utility_score),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{name} deve estar entre 0 e 100."
                )
