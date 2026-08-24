from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class CompositionSnapshot:
    match_id: str
    placement: int

    carry_character_id: str = ""
    tank_character_id: str = ""
    support_character_id: str = ""

    unit_ids: tuple[str, ...] = field(
        default_factory=tuple
    )
    trait_names: tuple[str, ...] = field(
        default_factory=tuple
    )

    composition_key: str = ""

    def __post_init__(self) -> None:
        if not self.match_id.strip():
            raise ValueError(
                "CompositionSnapshot.match_id não pode ser vazio."
            )

        if not 1 <= self.placement <= 8:
            raise ValueError(
                "CompositionSnapshot.placement deve estar entre 1 e 8."
            )

        if not self.composition_key.strip():
            raise ValueError(
                "CompositionSnapshot.composition_key não pode ser vazio."
            )
