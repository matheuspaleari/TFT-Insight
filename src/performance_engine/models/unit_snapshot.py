from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class UnitSnapshot:
    """Representa uma unidade no tabuleiro final do participante."""

    character_id: str
    name: str = ""
    rarity: int = 0
    tier: int = 1
    items: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.character_id.strip():
            raise ValueError(
                "UnitSnapshot.character_id não pode ser vazio."
            )

        if self.rarity < 0:
            raise ValueError(
                "UnitSnapshot.rarity não pode ser negativo."
            )

        if self.tier < 1:
            raise ValueError(
                "UnitSnapshot.tier deve ser maior que zero."
            )

        if any(not item.strip() for item in self.items):
            raise ValueError(
                "UnitSnapshot.items não pode conter nomes vazios."
            )
