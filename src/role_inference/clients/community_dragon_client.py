from typing import Any
import requests


class CommunityDragonClient:
    BASE_URL = "https://raw.communitydragon.org"

    def __init__(
        self,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get_tft_data(
        self,
        *,
        channel: str = "latest",
        locale: str = "pt_br",
    ) -> dict[str, Any]:
        url = (
            f"{self.BASE_URL}/{channel}/"
            f"cdragon/tft/{locale}.json"
        )

        try:
            response = self.session.get(
                url,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as error:
            raise RuntimeError(
                "Falha ao baixar dados completos "
                "do CommunityDragon."
            ) from error
        except ValueError as error:
            raise RuntimeError(
                "O CommunityDragon retornou JSON inválido."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                "Formato inesperado do CommunityDragon."
            )

        return data
