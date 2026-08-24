from dataclasses import dataclass, field

from .unit_role_assessment import UnitRoleAssessment


@dataclass(slots=True, frozen=True)
class ParticipantRoleReport:
    participant_puuid: str

    damage_carry: UnitRoleAssessment | None
    main_tank: UnitRoleAssessment | None
    support: UnitRoleAssessment | None

    assessments: tuple[UnitRoleAssessment, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.participant_puuid.strip():
            raise ValueError(
                "participant_puuid não pode ser vazio."
            )
