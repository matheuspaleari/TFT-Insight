from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class RichItemData:
    item_id: str
    name: str
    description: str = ""
    effects: dict[str, float] = field(default_factory=dict)
    raw_data: dict[str, Any] | None = None
