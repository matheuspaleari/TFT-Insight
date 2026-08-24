from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TraitSnapshot:
    """Representa o estado final de uma trait na partida."""

    name: str
    num_units: int = 0
    style: int = 0
    tier_current: int = 0
    tier_total: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "TraitSnapshot.name não pode ser vazio."
            )

        for field_name, value in (
            ("num_units", self.num_units),
            ("style", self.style),
            ("tier_current", self.tier_current),
            ("tier_total", self.tier_total),
        ):
            if value < 0:
                raise ValueError(
                    f"TraitSnapshot.{field_name} não pode ser negativo."
                )

    @property
    def is_active(self) -> bool:
        return self.style > 0 or self.tier_current > 0
