from typing import Any
from .models import (
    StaticDataCatalog,
    StaticItem,
    StaticTrait,
    StaticUnit,
)


class StaticDataParser:
    @classmethod
    def parse(
        cls,
        *,
        version: str,
        locale: str,
        champions_data: dict[str, Any],
        items_data: dict[str, Any],
        traits_data: dict[str, Any],
    ) -> StaticDataCatalog:
        return StaticDataCatalog(
            version=version,
            locale=locale,
            units=cls._units(champions_data),
            items=cls._items(items_data),
            traits=cls._traits(traits_data),
        )

    @staticmethod
    def _data(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data", {})
        return data if isinstance(data, dict) else {}

    @classmethod
    def _units(
        cls,
        payload: dict[str, Any],
    ) -> dict[str, StaticUnit]:
        result = {}
        for fallback_id, raw in cls._data(payload).items():
            if not isinstance(raw, dict):
                continue
            unit_id = str(raw.get("id", fallback_id) or fallback_id)
            name = str(raw.get("name", unit_id) or unit_id)
            image = raw.get("image", {})
            try:
                tier = int(raw.get("tier", 0))
            except (TypeError, ValueError):
                tier = 0
            result[unit_id] = StaticUnit(
                character_id=unit_id,
                name=name,
                tier=max(tier, 0),
                image_full=(
                    str(image.get("full", "") or "")
                    if isinstance(image, dict)
                    else ""
                ),
                raw_data=raw,
            )
        return result

    @classmethod
    def _items(
        cls,
        payload: dict[str, Any],
    ) -> dict[str, StaticItem]:
        result = {}
        for fallback_id, raw in cls._data(payload).items():
            if not isinstance(raw, dict):
                continue
            item_id = str(raw.get("id", fallback_id) or fallback_id)
            image = raw.get("image", {})
            result[item_id] = StaticItem(
                item_id=item_id,
                name=str(raw.get("name", item_id) or item_id),
                description=str(raw.get("description", "") or ""),
                image_full=(
                    str(image.get("full", "") or "")
                    if isinstance(image, dict)
                    else ""
                ),
                raw_data=raw,
            )
        return result

    @classmethod
    def _traits(
        cls,
        payload: dict[str, Any],
    ) -> dict[str, StaticTrait]:
        result = {}
        for fallback_id, raw in cls._data(payload).items():
            if not isinstance(raw, dict):
                continue
            trait_id = str(raw.get("id", fallback_id) or fallback_id)
            image = raw.get("image", {})
            result[trait_id] = StaticTrait(
                trait_id=trait_id,
                name=str(raw.get("name", trait_id) or trait_id),
                description=str(raw.get("description", "") or ""),
                image_full=(
                    str(image.get("full", "") or "")
                    if isinstance(image, dict)
                    else ""
                ),
                raw_data=raw,
            )
        return result
