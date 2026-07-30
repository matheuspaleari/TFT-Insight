"""
Cliente responsável por consultar os dados estáticos do Data Dragon.
"""

from typing import Any

import requests

from src.constants import REQUEST_TIMEOUT


class DataDragonClient:
    """
    Consulta versões e dados estáticos do TFT no Data Dragon.
    """

    BASE_URL = "https://ddragon.leagueoflegends.com"
    DEFAULT_LOCALE = "pt_BR"

    def __init__(
        self,
        locale: str = DEFAULT_LOCALE
    ) -> None:
        self.locale = locale
        self.session = requests.Session()

    def get_latest_version(self) -> str:
        """
        Retorna a versão mais recente disponível no Data Dragon.
        """

        url = f"{self.BASE_URL}/api/versions.json"

        data = self._get_json(url)

        if not isinstance(data, list) or not data:
            raise RuntimeError(
                "O Data Dragon não retornou nenhuma versão disponível."
            )

        return str(data[0])

    def get_tft_traits(
        self,
        version: str | None = None
    ) -> dict[str, Any]:
        """
        Retorna os dados estáticos das traits de TFT.

        Caso a versão não seja informada, utiliza a mais recente.
        """

        selected_version = version or self.get_latest_version()

        url = (
            f"{self.BASE_URL}/cdn/{selected_version}"
            f"/data/{self.locale}/tft-trait.json"
        )

        data = self._get_json(url)

        traits = data.get("data")

        if not isinstance(traits, dict):
            raise RuntimeError(
                "O Data Dragon não retornou os dados de traits esperados."
            )

        return traits

    def _get_json(
        self,
        url: str
    ) -> Any:
        """
        Executa uma requisição GET e retorna o JSON.
        """

        try:
            response = self.session.get(
                url=url,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout as error:
            raise RuntimeError(
                "O Data Dragon demorou muito para responder."
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                "Não foi possível conectar ao Data Dragon."
            ) from error

        except requests.exceptions.HTTPError as error:
            raise RuntimeError(
                "Erro ao consultar o Data Dragon. "
                f"Status HTTP: {error.response.status_code}"
            ) from error

        except requests.exceptions.JSONDecodeError as error:
            raise RuntimeError(
                "O Data Dragon retornou um conteúdo inválido."
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Erro inesperado ao consultar o Data Dragon: {error}"
            ) from error