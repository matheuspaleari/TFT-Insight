from dataclasses import dataclass, field

from .unit_role import UnitRole


@dataclass(slots=True, frozen=True)
class UnitRoleAssessment:
    character_id: str
    role: UnitRole
    confidence: float

    offense_score: float
    defense_score: float
    utility_score: float

    item_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.character_id.strip():
            raise ValueError(
                "character_id não pode ser vazio."
            )

        for field_name, value in (
            ("confidence", self.confidence),
            ("offense_score", self.offense_score),
            ("defense_score", self.defense_score),
            ("utility_score", self.utility_score),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )
