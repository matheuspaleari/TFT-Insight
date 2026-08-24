import json
from pathlib import Path

from src.role_inference.models import ItemObservation


class ItemObservationRepository:
    def __init__(
        self,
        path: str | Path = (
            "data/role_inference/"
            "item_observations.json"
        ),
    ) -> None:
        self.path = Path(path)

    def load_all(self) -> dict[str, ItemObservation]:
        if not self.path.exists():
            return {}

        raw = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        return {
            item_id: ItemObservation(
                item_id=item_id,
                **values,
            )
            for item_id, values in raw.items()
            if isinstance(values, dict)
        }

    def save_all(
        self,
        observations: dict[str, ItemObservation],
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            item_id: {
                "frontline_uses": observation.frontline_uses,
                "backline_uses": observation.backline_uses,
                "damage_carry_uses": observation.damage_carry_uses,
                "tank_uses": observation.tank_uses,
                "support_uses": observation.support_uses,
            }
            for item_id, observation
            in observations.items()
        }

        self.path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
