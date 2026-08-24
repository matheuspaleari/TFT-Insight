from .data_dragon_client import DataDragonClient
from .models import StaticDataCatalog
from .static_data_parser import StaticDataParser
from .static_data_repository import StaticDataRepository


class StaticDataUpdateService:
    REQUIRED_FILES = (
        "tft-champion.json",
        "tft-item.json",
        "tft-trait.json",
    )

    def __init__(
        self,
        *,
        client: DataDragonClient,
        repository: StaticDataRepository,
        locale: str = "pt_BR",
        max_versions_to_try: int = 12,
    ) -> None:
        self.client = client
        self.repository = repository
        self.locale = locale
        self.max_versions_to_try = max_versions_to_try

    def load_latest(
        self,
        *,
        force_refresh: bool = False,
    ) -> StaticDataCatalog:
        try:
            versions = self.client.get_versions()
            for version in versions[:self.max_versions_to_try]:
                if (
                    not force_refresh
                    and self.repository.has_complete_version(
                        version=version,
                        locale=self.locale,
                    )
                ):
                    return self._load(version)

                downloaded = self._download(version)
                if downloaded is not None:
                    return downloaded
        except RuntimeError as error:
            print(f"Falha ao atualizar dados estáticos: {error}")

        for version in self.repository.list_cached_versions(
            self.locale
        ):
            if self.repository.has_complete_version(
                version=version,
                locale=self.locale,
            ):
                print(f"Usando cache estático: {version}")
                return self._load(version)

        raise RuntimeError(
            "Nenhuma versão estática válida foi encontrada."
        )

    def _download(
        self,
        version: str,
    ) -> StaticDataCatalog | None:
        payloads = {}
        try:
            for filename in self.REQUIRED_FILES:
                print(f"Testando {version}: {filename}")
                payloads[filename] = self.client.get_tft_file(
                    version=version,
                    locale=self.locale,
                    filename=filename,
                )
        except RuntimeError:
            return None

        for filename, data in payloads.items():
            self.repository.save(
                version=version,
                locale=self.locale,
                filename=filename,
                data=data,
            )

        print(f"Dados estáticos atualizados: {version}")
        return self._parse(version, payloads)

    def _load(self, version: str) -> StaticDataCatalog:
        payloads = {
            filename: self.repository.load(
                version=version,
                locale=self.locale,
                filename=filename,
            )
            for filename in self.REQUIRED_FILES
        }
        return self._parse(version, payloads)

    def _parse(
        self,
        version: str,
        payloads: dict,
    ) -> StaticDataCatalog:
        return StaticDataParser.parse(
            version=version,
            locale=self.locale,
            champions_data=payloads["tft-champion.json"],
            items_data=payloads["tft-item.json"],
            traits_data=payloads["tft-trait.json"],
        )
