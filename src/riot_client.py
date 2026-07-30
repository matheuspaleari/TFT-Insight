"""
Cliente responsável pela comunicação com a Riot Games API.
"""

from itertools import count
from typing import Any
from urllib import response
from urllib.parse import quote

import requests

from src.config import Config
from src.constants import REGION, REQUEST_TIMEOUT


class RiotClient:
    """
    Cliente para realizar requisições à Riot Games API.
    """

    def __init__(self) -> None:
        if not Config.RIOT_API_KEY:
            raise ValueError(
                "A variável RIOT_API_KEY não foi encontrada no arquivo .env."
            )

        self.api_key = Config.RIOT_API_KEY

        self.headers = {
            "X-Riot-Token": self.api_key
        }

    def get_account(
        self,
        game_name: str,
        tag_line: str
    ) -> dict[str, Any]:
        """
        Busca os dados de uma conta Riot utilizando o Riot ID.

        Args:
            game_name: Nome do jogador, sem a tag.
            tag_line: Tag do jogador, sem o caractere #.

        Returns:
            Dicionário contendo PUUID, gameName e tagLine.

        Raises:
            ValueError: Quando o Riot ID estiver incompleto.
            requests.HTTPError: Quando a API retornar um erro HTTP.
        """

        if not game_name or not tag_line:
            raise ValueError(
                "O nome do jogador e a tag devem ser informados."
            )

        encoded_game_name = quote(game_name, safe="")
        encoded_tag_line = quote(tag_line, safe="")

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/"
            f"{encoded_game_name}/{encoded_tag_line}"
        )

        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout as error:
            raise RuntimeError(
                "A Riot API demorou muito para responder."
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                "Não foi possível conectar à Riot API."
            ) from error

        except requests.exceptions.HTTPError:
            self._handle_http_error(response)

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Erro inesperado ao consultar a Riot API: {error}"
            ) from error

    def get_puuid(
        self,
        game_name: str,
        tag_line: str
    ) -> str:
        """
        Retorna apenas o PUUID do jogador.
        """

        account = self.get_account(
            game_name,
            tag_line
        )

        return account["puuid"]


    def get_match_ids(
        self,
        puuid: str,
        count: int = 20
    ) -> list[str]:
        """
        Busca os IDs das últimas partidas de TFT de um jogador.

        Args:
            puuid: Identificador único do jogador.
            count: Quantidade de partidas que será retornada.

     Returns:
         Lista contendo os IDs das partidas.
     """

        if not puuid:
            raise ValueError("O PUUID do jogador deve ser informado.")

        if count < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/tft/match/v1/matches/by-puuid/"
            f"{puuid}/ids"
        )

        params = {
            "count": count
        }

        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout as error:
            raise RuntimeError(
                "A Riot API demorou muito para retornar as partidas."
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                "Não foi possível conectar à Riot API."
            ) from error

        except requests.exceptions.HTTPError:
            self._handle_http_error(response)

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Erro inesperado ao buscar as partidas: {error}"
            ) from error
    
    def get_match_details(
        self,
        match_id: str
    ) -> dict[str, Any]:
        """
        Busca os detalhes completos de uma partida de TFT.

        Args:
            match_id: Identificador da partida.

        Returns:
            Dicionário com os dados completos da partida.
        """

        if not match_id:
            raise ValueError("O ID da partida deve ser informado.")

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/tft/match/v1/matches/{match_id}"
        )

        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout as error:
            raise RuntimeError(
                "A Riot API demorou muito para retornar a partida."
            ) from error

        except requests.exceptions.ConnectionError as error:
            raise RuntimeError(
                "Não foi possível conectar à Riot API."
            ) from error

        except requests.exceptions.HTTPError:
            self._handle_http_error(response)

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Erro inesperado ao buscar a partida: {error}"
            ) from error

    
    @staticmethod
    def _handle_http_error(response: requests.Response) -> None:
        """
        Converte os principais códigos HTTP em mensagens mais claras.
        """

        status_messages = {
            400: "A requisição enviada para a Riot API é inválida.",
            401: "A Riot API Key é inválida ou não foi informada.",
            403: (
                "A Riot API Key expirou ou não possui permissão. "
                "Gere uma nova chave no Riot Developer Portal."
            ),
            404: "Jogador não encontrado. Verifique o Riot ID e a tag.",
            429: (
                "Limite de requisições atingido. "
                "Aguarde alguns segundos e tente novamente."
            ),
            500: "A Riot API apresentou um erro interno.",
            502: "A Riot API está temporariamente indisponível.",
            503: "O serviço da Riot API está indisponível.",
            504: "A Riot API demorou muito para responder."
        }

        message = status_messages.get(
            response.status_code,
            (
                "Erro ao consultar a Riot API. "
                f"Status HTTP: {response.status_code}"
            )
        )

        raise RuntimeError(message)

