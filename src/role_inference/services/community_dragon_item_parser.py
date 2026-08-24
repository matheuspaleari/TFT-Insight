from typing import Any

from src.role_inference.models import RichItemData


class CommunityDragonItemParser:
    """
    Localiza itens mesmo que a estrutura do JSON mude.

    O parser percorre o documento recursivamente e reconhece objetos
    contendo apiName/id e nome. Isso reduz acoplamento ao formato exato.
    """

    @classmethod
    def parse(
        cls,
        payload: dict[str, Any],
    ) -> dict[str, RichItemData]:
        items: dict[str, RichItemData] = {}

        for candidate in cls._walk(payload):
            parsed = cls._parse_candidate(candidate)

            if parsed is None:
                continue

            current = items.get(parsed.item_id)

            if (
                current is None
                or cls._quality(parsed)
                > cls._quality(current)
            ):
                items[parsed.item_id] = parsed

        return items

    @classmethod
    def _walk(
        cls,
        value: Any,
    ):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from cls._walk(child)

        elif isinstance(value, list):
            for child in value:
                yield from cls._walk(child)

    @classmethod
    def _parse_candidate(
        cls,
        raw: dict[str, Any],
    ) -> RichItemData | None:
        item_id = str(
            raw.get("apiName")
            or raw.get("id")
            or ""
        ).strip()

        name = str(
            raw.get("name")
            or raw.get("displayName")
            or ""
        ).strip()

        if (
            not item_id
            or not name
            or "Item" not in item_id
        ):
            return None

        description = str(
            raw.get("desc")
            or raw.get("description")
            or raw.get("tooltip")
            or ""
        ).strip()

        effects = cls._extract_effects(
            raw.get("effects", {})
        )

        return RichItemData(
            item_id=item_id,
            name=name,
            description=description,
            effects=effects,
            raw_data=raw,
        )

    @staticmethod
    def _extract_effects(
        raw_effects: Any,
    ) -> dict[str, float]:
        if not isinstance(raw_effects, dict):
            return {}

        effects = {}

        for key, value in raw_effects.items():
            try:
                effects[str(key)] = float(value)
            except (TypeError, ValueError):
                continue

        return effects

    @staticmethod
    def _quality(item: RichItemData) -> int:
        return (
            int(bool(item.description)) * 10
            + len(item.effects)
        )
