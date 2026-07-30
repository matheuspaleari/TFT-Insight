"""
Mapeamento dos identificadores técnicos das traits para nomes amigáveis.
"""

from typing import Any

from src.assets.data_dragon import DataDragonClient


class TraitMapper:
    """
    Traduz IDs técnicos de traits utilizando o Data Dragon.
    """

    def __init__(
        self,
        data_dragon_client: DataDragonClient | None = None
    ) -> None:
        self.client = (
            data_dragon_client
            if data_dragon_client is not None
            else DataDragonClient(locale="pt_BR")
        )

        self._mapping: dict[str, str] = {}
        self._loaded = False

    def load(self) -> None:
        """
        Carrega o mapeamento de traits somente uma vez.
        """

        if self._loaded:
            return

        traits_data = self.client.get_tft_traits()

        self._mapping = self._build_mapping(
            traits_data
        )

        self._loaded = True

    def translate(
        self,
        trait_id: str | None
    ) -> str:
        """
        Traduz o ID técnico de uma trait.

        Se o ID não estiver no Data Dragon, retorna uma versão
        simplificada do próprio identificador.
        """

        if not trait_id:
            return "Trait desconhecida"

        if not self._loaded:
            self.load()

        translated_name = self._mapping.get(trait_id)

        if translated_name:
            return translated_name

        return self._fallback_name(trait_id)

    @staticmethod
    def _build_mapping(
        traits_data: dict[str, Any]
    ) -> dict[str, str]:
        """
        Constrói o dicionário ID → nome traduzido.
        """

        mapping: dict[str, str] = {}

        for trait_key, trait_data in traits_data.items():
            if not isinstance(trait_data, dict):
                continue

            trait_id = trait_data.get("id") or trait_key
            trait_name = trait_data.get("name")

            if trait_id and trait_name:
                mapping[str(trait_id)] = str(trait_name)

            if trait_key and trait_name:
                mapping[str(trait_key)] = str(trait_name)

        return mapping

    @staticmethod
    def _fallback_name(
        trait_id: str
    ) -> str:
        """
        Simplifica um identificador técnico não encontrado.
        """

        name = trait_id

        if name.startswith("TFT"):
            parts = name.split("_", maxsplit=1)

            if len(parts) == 2:
                name = parts[1]

        name = name.replace("UniqueTrait", "")
        name = name.replace("Trait", "")

        return name or trait_id