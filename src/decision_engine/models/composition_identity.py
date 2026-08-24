from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class CompositionIdentity:
    carry_character_id: str = ""
    tank_character_id: str = ""
    support_character_id: str = ""

    primary_trait_names: tuple[str, ...] = field(
        default_factory=tuple
    )
    core_unit_ids: tuple[str, ...] = field(
        default_factory=tuple
    )

    identity_key: str = ""

    def __post_init__(self) -> None:
        if not self.identity_key.strip():
            raise ValueError(
                "CompositionIdentity.identity_key não pode ser vazio."
            )

    @property
    def display_name(self) -> str:
        parts = [*self.primary_trait_names]

        if self.carry_character_id:
            parts.append(self.carry_character_id)

        if self.tank_character_id:
            parts.append(
                f"Tank: {self.tank_character_id}"
            )

        return " · ".join(parts) or self.identity_key
