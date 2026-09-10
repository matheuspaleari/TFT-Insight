from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ItemManualCatalogRepository:
    """
    Repositório do catálogo manual de itens do Set 18.

    Regras:
    - riot_item_id é a chave interna autoritativa;
    - display_name é apenas apresentação;
    - classificação manual nunca é alterada pelo benchmark;
    - itens ausentes do catálogo podem seguir pelo classificador legado.
    """

    SCHEMA_VERSION = "2.0"
    SET_NUMBER = 18
    SET_CORE_NAME = "TFTSet18"

    def __init__(
        self,
        path: Path | str | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self.path = (
            Path(path)
            if path is not None
            else project_root
            / "data"
            / "role_inference"
            / "set18"
            / "item_catalog_v2.json"
        )

    def exists(self) -> bool:
        return self.path.is_file()

    def load(self) -> dict[str, Any]:
        if not self.exists():
            raise FileNotFoundError(
                "Catálogo manual de itens não encontrado: "
                f"{self.path}"
            )

        payload = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        self._validate_payload(payload)
        return payload

    def load_items(self) -> dict[str, dict[str, Any]]:
        payload = self.load()
        result: dict[str, dict[str, Any]] = {}

        for raw in payload["items"]:
            item_id = str(
                raw.get("riot_item_id", "")
            ).strip()

            if item_id in result:
                raise ValueError(
                    "riot_item_id duplicado no catálogo: "
                    f"{item_id}"
                )

            result[item_id] = raw

        return result

    def get(
        self,
        riot_item_id: str,
    ) -> dict[str, Any] | None:
        item_id = str(riot_item_id or "").strip()
        if not item_id:
            return None

        return self.load_items().get(item_id)

    @classmethod
    def _validate_payload(
        cls,
        payload: Any,
    ) -> None:
        if not isinstance(payload, dict):
            raise ValueError(
                "item_catalog_v2.json deve conter um objeto JSON."
            )

        if payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError(
                "schema_version inválido no catálogo de itens. "
                f"Esperado: {cls.SCHEMA_VERSION!r}."
            )

        set_data = payload.get("set")
        if not isinstance(set_data, dict):
            raise ValueError(
                "Bloco 'set' ausente ou inválido no catálogo."
            )

        if set_data.get("number") != cls.SET_NUMBER:
            raise ValueError(
                "Número do set inválido no catálogo de itens."
            )

        if set_data.get("core_name") != cls.SET_CORE_NAME:
            raise ValueError(
                "core_name inválido no catálogo de itens."
            )

        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError(
                "Campo 'items' deve ser uma lista."
            )

        seen: set[str] = set()

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Item #{index} possui formato inválido."
                )

            item_id = str(
                item.get("riot_item_id", "")
            ).strip()

            if not item_id:
                raise ValueError(
                    f"Item #{index} não possui riot_item_id."
                )

            if item_id in seen:
                raise ValueError(
                    f"riot_item_id duplicado: {item_id}"
                )

            seen.add(item_id)

            display_name = str(
                item.get("display_name", "")
            ).strip()

            if not display_name:
                raise ValueError(
                    f"{item_id}: display_name vazio."
                )

            if item.get("manual_verified") is not True:
                raise ValueError(
                    f"{item_id}: manual_verified deve ser true."
                )

            for field in (
                "carry_weight",
                "tank_weight",
                "support_weight",
            ):
                value = item.get(field)

                if (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not 0 <= float(value) <= 100
                ):
                    raise ValueError(
                        f"{item_id}: {field} deve estar "
                        "entre 0 e 100."
                    )

            if not isinstance(
                item.get("learning_enabled"),
                bool,
            ):
                raise ValueError(
                    f"{item_id}: learning_enabled deve ser booleano."
                )
