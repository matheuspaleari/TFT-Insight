from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class StaticUnit:
    character_id: str
    name: str
    tier: int = 0
    image_full: str = ""
    raw_data: dict[str, Any] | None = None


@dataclass(slots=True, frozen=True)
class StaticItem:
    item_id: str
    name: str
    description: str = ""
    image_full: str = ""
    raw_data: dict[str, Any] | None = None


@dataclass(slots=True, frozen=True)
class StaticTrait:
    trait_id: str
    name: str
    description: str = ""
    image_full: str = ""
    raw_data: dict[str, Any] | None = None


@dataclass(slots=True, frozen=True)
class StaticDataCatalog:
    version: str
    locale: str
    units: dict[str, StaticUnit] = field(default_factory=dict)
    items: dict[str, StaticItem] = field(default_factory=dict)
    traits: dict[str, StaticTrait] = field(default_factory=dict)

    def get_unit(self, character_id: str) -> StaticUnit | None:
        return self.units.get(character_id)

    def get_item(self, item_id: str) -> StaticItem | None:
        return self.items.get(item_id)

    def get_trait(self, trait_id: str) -> StaticTrait | None:
        return self.traits.get(trait_id)
