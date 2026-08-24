from dataclasses import dataclass, field

from .item_category import ItemCategory


@dataclass(slots=True, frozen=True)
class ItemClassification:
    item_id: str
    category: ItemCategory
    confidence: float

    offense_score: float
    defense_score: float
    utility_score: float

    evidence: tuple[str, ...] = field(default_factory=tuple)
    source: str = "unknown"

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id não pode ser vazio.")

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
