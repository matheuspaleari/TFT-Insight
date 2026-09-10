from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class UnitCatalogEntry:
    character_id: str
    display_name: str
    cost: int
    primary_role: str
    role_label: str
    carry_eligible: bool
    unit_type: str


class UnitCatalogRepository:
    """
    Leitor do catálogo manual de unidades do Set 18.

    O character_id é usado apenas como chave técnica interna.
    Para apresentação ao usuário, use sempre display_name.
    """

    DEFAULT_PATH = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "role_inference"
        / "set18"
        / "unit_catalog_v2.json"
    )

    _cache: dict[str, UnitCatalogEntry] | None = None
    _cache_path: Path | None = None

    @classmethod
    def load_all(
        cls,
        path: Path | None = None,
        *,
        force_reload: bool = False,
    ) -> dict[str, UnitCatalogEntry]:
        catalog_path = (path or cls.DEFAULT_PATH).resolve()

        if (
            not force_reload
            and cls._cache is not None
            and cls._cache_path == catalog_path
        ):
            return cls._cache

        if not catalog_path.exists():
            raise FileNotFoundError(
                "Catálogo de unidades não encontrado em: "
                f"{catalog_path}"
            )

        try:
            payload = json.loads(
                catalog_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"JSON inválido no catálogo de unidades: {catalog_path}"
            ) from exc

        units = payload.get("units")
        if not isinstance(units, list):
            raise ValueError(
                "unit_catalog_v2.json deve possuir uma lista 'units'."
            )

        parsed: dict[str, UnitCatalogEntry] = {}

        for index, raw in enumerate(units, start=1):
            if not isinstance(raw, dict):
                raise ValueError(
                    f"Entrada #{index} do catálogo não é um objeto."
                )

            entry = cls._parse_entry(raw=raw, index=index)

            if entry.character_id in parsed:
                raise ValueError(
                    "character_id duplicado no catálogo: "
                    f"{entry.character_id}"
                )

            parsed[entry.character_id] = entry

        if not parsed:
            raise ValueError(
                "O catálogo de unidades está vazio."
            )

        cls._cache = parsed
        cls._cache_path = catalog_path
        return parsed

    @classmethod
    def get(
        cls,
        character_id: str,
        path: Path | None = None,
    ) -> UnitCatalogEntry | None:
        key = str(character_id or "").strip()
        if not key:
            return None

        return cls.load_all(path=path).get(key)

    @classmethod
    def display_name(
        cls,
        character_id: str,
        fallback: str = "",
        path: Path | None = None,
    ) -> str:
        """
        Nome seguro para UI.

        Nunca devolve character_id como fallback automaticamente.
        Se o ID não existir no catálogo, prefere o nome já fornecido
        pelo snapshot. Se também estiver vazio, devolve "Unidade".
        """

        entry = cls.get(character_id=character_id, path=path)
        if entry is not None and entry.display_name.strip():
            return entry.display_name.strip()

        clean_fallback = str(fallback or "").strip()
        if clean_fallback:
            return clean_fallback

        return "Unidade"

    @staticmethod
    def _parse_entry(
        *,
        raw: dict[str, Any],
        index: int,
    ) -> UnitCatalogEntry:
        character_id = str(
            raw.get("character_id") or ""
        ).strip()
        display_name = str(
            raw.get("display_name") or ""
        ).strip()
        primary_role = str(
            raw.get("primary_role") or ""
        ).strip()
        role_label = str(
            raw.get("role_label") or ""
        ).strip()
        unit_type = str(
            raw.get("unit_type") or ""
        ).strip()

        try:
            cost = int(raw.get("cost"))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Entrada #{index}: cost inválido."
            ) from exc

        carry_eligible = raw.get("carry_eligible")
        if not isinstance(carry_eligible, bool):
            raise ValueError(
                f"Entrada #{index}: carry_eligible deve ser booleano."
            )

        required = {
            "character_id": character_id,
            "display_name": display_name,
            "primary_role": primary_role,
            "role_label": role_label,
            "unit_type": unit_type,
        }

        missing = [
            name
            for name, value in required.items()
            if not value
        ]

        if missing:
            raise ValueError(
                f"Entrada #{index}: campos vazios: {', '.join(missing)}"
            )

        if cost < 1:
            raise ValueError(
                f"Entrada #{index}: cost deve ser >= 1."
            )

        return UnitCatalogEntry(
            character_id=character_id,
            display_name=display_name,
            cost=cost,
            primary_role=primary_role,
            role_label=role_label,
            carry_eligible=carry_eligible,
            unit_type=unit_type,
        )
