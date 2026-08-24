from typing import Any
import requests


class DataDragonClient:
    BASE_URL = "https://ddragon.leagueoflegends.com"
    VERSIONS_URL = f"{BASE_URL}/api/versions.json"

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get_versions(self) -> list[str]:
        data = self._get_json(self.VERSIONS_URL)
        if not isinstance(data, list):
            raise RuntimeError("Lista de versões inválida.")
        return [str(version) for version in data]

    def get_tft_file(
        self,
        *,
        version: str,
        locale: str,
        filename: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.BASE_URL}/cdn/{version}/data/"
            f"{locale}/{filename}"
        )
        data = self._get_json(url)
        if not isinstance(data, dict):
            raise RuntimeError(f"Formato inválido em {filename}.")
        return data

    def _get_json(self, url: str) -> Any:
        try:
            response = self.session.get(
                url,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout as error:
            raise RuntimeError(
                "O Data Dragon demorou para responder."
            ) from error
        except requests.ConnectionError as error:
            raise RuntimeError(
                "Não foi possível conectar ao Data Dragon."
            ) from error
        except requests.HTTPError as error:
            code = (
                error.response.status_code
                if error.response is not None
                else "desconhecido"
            )
            raise RuntimeError(
                f"Falha HTTP {code} ao buscar {url}"
            ) from error
        except ValueError as error:
            raise RuntimeError(
                "O Data Dragon retornou JSON inválido."
            ) from error
