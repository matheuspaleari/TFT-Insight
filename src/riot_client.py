"""
Cliente responsável pela comunicação com a Riot Games API.
"""

import time
from typing import Any
from urllib.parse import quote

import requests

from src.config import Config
from src.constants import PLATFORM, REGION, REQUEST_TIMEOUT


class RiotClient:
    """
    Cliente para realizar requisições à Riot Games API.

    Centraliza autenticação, requisições GET, controle preventivo
    de frequência e novas tentativas quando o limite da API é atingido.
    """

    MIN_REQUEST_INTERVAL_SECONDS = 1.3
    MAX_RETRIES = 5
    DEFAULT_RETRY_AFTER_SECONDS = 15.0

    """
    Cliente para realizar requisições à Riot Games API.

    Centraliza autenticação, requisições GET e tratamento
    dos principais erros retornados pela API.
    """

    def __init__(self) -> None:
        if not Config.RIOT_API_KEY:
            raise ValueError(
                "A variável RIOT_API_KEY não foi encontrada no arquivo .env."
            )

        self.api_key = Config.RIOT_API_KEY

        self.headers = {
            "X-Riot-Token": self.api_key,
        }

        self._last_request_at = 0.0

    def get_account(
        self,
        game_name: str,
        tag_line: str,
    ) -> dict[str, Any]:
        """
        Busca uma conta Riot utilizando o Riot ID.

        Args:
            game_name: Nome do jogador, sem a tag.
            tag_line: Tag do jogador, sem o caractere #.

        Returns:
            Dicionário contendo dados como puuid, gameName e tagLine.
        """

        if not game_name.strip() or not tag_line.strip():
            raise ValueError(
                "O nome do jogador e a tag devem ser informados."
            )

        encoded_game_name = quote(game_name.strip(), safe="")
        encoded_tag_line = quote(tag_line.strip(), safe="")

        url = (
            f"https://{REGION}.api.riotgames.com"
            "/riot/account/v1/accounts/by-riot-id/"
            f"{encoded_game_name}/{encoded_tag_line}"
        )

        data = self._get(
            url=url,
            timeout_message=(
                "A Riot API demorou muito para retornar a conta."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar a conta."
            ),
            unexpected_message="Erro inesperado ao buscar a conta",
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "A Riot API retornou um formato inválido para a conta."
            )

        return data


    def get_account_by_puuid(
        self,
        puuid: str,
    ) -> dict[str, Any]:
        """
        Busca os dados de uma conta Riot utilizando o PUUID.

        Args:
            puuid: Identificador único da conta Riot.

        Returns:
            Dicionário contendo dados como puuid, gameName e tagLine.
        """

        if not puuid.strip():
            raise ValueError(
                "O PUUID do jogador deve ser informado."
            )

        encoded_puuid = quote(puuid.strip(), safe="")

        url = (
            f"https://{REGION}.api.riotgames.com"
            "/riot/account/v1/accounts/by-puuid/"
            f"{encoded_puuid}"
        )

        data = self._get(
            url=url,
            timeout_message=(
                "A Riot API demorou muito para retornar a conta."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar a conta pelo PUUID."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar a conta pelo PUUID"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "A Riot API retornou um formato inválido para a conta."
            )

        return data

    def get_player_name(
        self,
        puuid: str,
    ) -> str:
        """
        Retorna o Riot ID no formato gameName#tagLine.
        """

        account = self.get_account_by_puuid(puuid=puuid)

        game_name = account.get("gameName")
        tag_line = account.get("tagLine")

        if not isinstance(game_name, str) or not game_name.strip():
            raise RuntimeError(
                "A Riot API não retornou um gameName válido."
            )

        if not isinstance(tag_line, str) or not tag_line.strip():
            raise RuntimeError(
                "A Riot API não retornou uma tagLine válida."
            )

        return f"{game_name.strip()}#{tag_line.strip()}"

    def get_puuid(
        self,
        game_name: str,
        tag_line: str,
    ) -> str:
        """
        Busca e retorna somente o PUUID de uma conta Riot.
        """

        account = self.get_account(
            game_name=game_name,
            tag_line=tag_line,
        )

        puuid = account.get("puuid")

        if not isinstance(puuid, str) or not puuid:
            raise RuntimeError(
                "A Riot API não retornou um PUUID válido."
            )

        return puuid

    def get_match_ids(
        self,
        puuid: str,
        count: int = 20,
        start: int = 0,
    ) -> list[str]:
        """
        Busca IDs de partidas recentes de TFT.

        Args:
            puuid: Identificador único do jogador.
            count: Quantidade de partidas solicitadas.
            start: Índice inicial usado para paginação.

        Returns:
            Lista contendo os IDs das partidas.
        """

        if not puuid.strip():
            raise ValueError(
                "O PUUID do jogador deve ser informado."
            )

        if count < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )

        if start < 0:
            raise ValueError(
                "O índice inicial não pode ser negativo."
            )

        url = (
            f"https://{REGION}.api.riotgames.com"
            "/tft/match/v1/matches/by-puuid/"
            f"{puuid}/ids"
        )

        data = self._get(
            url=url,
            params={
                "start": start,
                "count": count,
            },
            timeout_message=(
                "A Riot API demorou muito para retornar as partidas."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar as partidas."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar os IDs das partidas"
            ),
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "A Riot API retornou um formato inválido "
                "para os IDs das partidas."
            )

        return [
            match_id
            for match_id in data
            if isinstance(match_id, str)
        ]

    def get_match_details(
        self,
        match_id: str,
    ) -> dict[str, Any]:
        """
        Busca os detalhes completos de uma partida de TFT.

        Args:
            match_id: Identificador da partida.

        Returns:
            Dicionário com os dados completos da partida.
        """

        if not match_id.strip():
            raise ValueError(
                "O ID da partida deve ser informado."
            )

        url = (
            f"https://{REGION}.api.riotgames.com"
            f"/tft/match/v1/matches/{match_id}"
        )

        data = self._get(
            url=url,
            timeout_message=(
                "A Riot API demorou muito para retornar a partida."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar a partida."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar os detalhes da partida"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "A Riot API retornou um formato inválido "
                "para os detalhes da partida."
            )

        return data

    def get_ranked_entries(
        self,
        *,
        puuid: str,
    ) -> list[dict[str, Any]]:
        """

        Busca as entradas ranqueadas de TFT de um jogador.

        Um jogador pode possuir entradas para filas diferentes,
        como TFT tradicional e Double Up.
        """

        if not puuid.strip():
            raise ValueError(
                "O PUUID do jogador deve ser informado."
            )

        encoded_puuid = quote(
            puuid.strip(),
            safe="",
        )

        url = (
            f"https://{PLATFORM}.api.riotgames.com"
            "/tft/league/v1/by-puuid/"
            f"{encoded_puuid}"
        )

        data = self._get(
            url=url,
            timeout_message=(
                "A Riot API demorou muito para retornar "
                "os dados ranqueados do jogador."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar os dados ranqueados."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar "
                "os dados ranqueados do jogador"
            ),
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "A Riot API retornou um formato inválido "
                "para os dados ranqueados."
            )

        return [
            entry
            for entry in data
            if isinstance(entry, dict)
        ]

    def get_ranked_tft_entry(
        self,
        *,
        puuid: str,
        queue_type: str = "RANKED_TFT",
    ) -> dict[str, Any] | None:
        """
        Retorna a entrada da fila ranqueada tradicional de TFT.

        Retorna None quando o jogador não possui elo nessa fila.
        """

        if not queue_type.strip():
            raise ValueError(
                "O tipo da fila deve ser informado."
            )

        normalized_queue_type = (
            queue_type.strip().upper()
        )

        entries = self.get_ranked_entries(
            puuid=puuid,
        )

        for entry in entries:
            if (
                str(
                    entry.get(
                        "queueType",
                        "",
                    )
                ).upper()
                == normalized_queue_type
            ):
                return entry

        return None

    def get_current_tft_tier(
        self,
        *,
        puuid: str,
    ) -> str | None:
        """
        Retorna somente o tier atual do TFT ranqueado.

        Exemplos:
            GOLD
            DIAMOND
            MASTER

        Retorna None quando o jogador não está ranqueado.
        """

        entry = self.get_ranked_tft_entry(
            puuid=puuid,
        )

        if entry is None:
            return None

        tier = entry.get("tier")

        if not isinstance(tier, str):
            return None

        normalized_tier = tier.strip().upper()

        if not normalized_tier:
            return None

        return normalized_tier
    
  
    def get_league_entries(
        self,
        *,
        tier: str,
        division: str,
        page: int = 1,
        queue: str = "RANKED_TFT",
    ) -> list[dict[str, Any]]:
        """
        Busca entradas ranqueadas de TFT para um elo e divisão.

        Este endpoint é utilizado para os elos com divisões:
        IRON, BRONZE, SILVER, GOLD, PLATINUM,
        EMERALD e DIAMOND.
        """

        normalized_tier = tier.strip().upper()
        normalized_division = division.strip().upper()
        normalized_queue = queue.strip().upper()

        valid_tiers = {
            "IRON",
            "BRONZE",
            "SILVER",
            "GOLD",
            "PLATINUM",
            "EMERALD",
            "DIAMOND",
        }

        valid_divisions = {
            "I",
            "II",
            "III",
            "IV",
        }

        if normalized_tier not in valid_tiers:
            raise ValueError(
                "O elo informado não possui divisões válidas "
                "para este endpoint."
            )

        if normalized_division not in valid_divisions:
            raise ValueError(
                "A divisão deve ser I, II, III ou IV."
            )

        if page < 1:
            raise ValueError(
                "A página deve ser maior que zero."
            )

        if not normalized_queue:
            raise ValueError(
                "A fila do ranking deve ser informada."
            )

        url = (
            f"https://{PLATFORM}.api.riotgames.com"
            "/tft/league/v1/entries/"
            f"{normalized_tier}/{normalized_division}"
        )

        data = self._get(
            url=url,
            params={
                "queue": normalized_queue,
                "page": page,
            },
            timeout_message=(
                "A Riot API demorou muito para retornar "
                "as entradas ranqueadas."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar as entradas ranqueadas."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar "
                "as entradas ranqueadas"
            ),
        )

        if not isinstance(data, list):
            raise RuntimeError(
                "A Riot API retornou um formato inválido "
                "para as entradas ranqueadas."
            )

        return [
            entry
            for entry in data
            if isinstance(entry, dict)
        ]

    def get_apex_league(
        self,
        *,
        tier: str,
        queue: str = "RANKED_TFT",
    ) -> dict[str, Any]:
        """
        Busca uma liga Apex de TFT.

        Elos suportados:
        MASTER, GRANDMASTER e CHALLENGER.
        """

        normalized_tier = tier.strip().upper()
        normalized_queue = queue.strip().upper()

        endpoint_by_tier = {
            "MASTER": "master",
            "GRANDMASTER": "grandmaster",
            "CHALLENGER": "challenger",
        }

        try:
            endpoint = endpoint_by_tier[
                normalized_tier
            ]
        except KeyError as error:
            raise ValueError(
                "O elo Apex deve ser MASTER, "
                "GRANDMASTER ou CHALLENGER."
            ) from error

        if not normalized_queue:
            raise ValueError(
                "A fila do ranking deve ser informada."
            )

        url = (
            f"https://{PLATFORM}.api.riotgames.com"
            f"/tft/league/v1/{endpoint}"
        )

        data = self._get(
            url=url,
            params={
                "queue": normalized_queue,
            },
            timeout_message=(
                "A Riot API demorou muito para retornar "
                f"a liga {normalized_tier}."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                f"para buscar a liga {normalized_tier}."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar "
                f"a liga {normalized_tier}"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "A Riot API retornou um formato inválido "
                f"para a liga {normalized_tier}."
            )

        return data

    def get_apex_league_players(
        self,
        *,
        tier: str,
        limit: int,
        queue: str = "RANKED_TFT",
    ) -> list[dict[str, Any]]:
        """
        Retorna jogadores de uma liga Apex ordenados
        por League Points.
        """

        if limit < 1:
            raise ValueError(
                "A quantidade de jogadores deve ser maior que zero."
            )

        league = self.get_apex_league(
            tier=tier,
            queue=queue,
        )

        entries = league.get(
            "entries",
            [],
        )

        if not isinstance(entries, list):
            raise RuntimeError(
                "A liga Apex não possui uma lista "
                "válida de jogadores."
            )

        valid_entries = [
            entry
            for entry in entries
            if isinstance(entry, dict)
        ]

        sorted_entries = sorted(
            valid_entries,
            key=lambda entry: entry.get(
                "leaguePoints",
                0,
            ),
            reverse=True,
        )

        return sorted_entries[:limit]

    def get_challenger_league(
        self,
        queue: str = "RANKED_TFT",
    ) -> dict[str, Any]:
        """
        Busca a liga Challenger de TFT da plataforma configurada.

        Args:
            queue: Tipo de fila ranqueada.
                O padrão representa o TFT ranqueado tradicional.

        Returns:
            Dicionário com os dados da liga e seus participantes.
        """

        if not queue.strip():
            raise ValueError(
                "A fila do ranking deve ser informada."
            )

        url = (
            f"https://{PLATFORM}.api.riotgames.com"
            "/tft/league/v1/challenger"
        )

        data = self._get(
            url=url,
            params={
                "queue": queue,
            },
            timeout_message=(
                "A Riot API demorou muito para retornar "
                "o ranking Challenger."
            ),
            connection_message=(
                "Não foi possível conectar à Riot API "
                "para buscar o ranking Challenger."
            ),
            unexpected_message=(
                "Erro inesperado ao buscar o ranking Challenger"
            ),
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "A Riot API retornou um formato inválido "
                "para o ranking Challenger."
            )

        return data

    def get_top_challenger_players(
        self,
        limit: int = 10,
        queue: str = "RANKED_TFT",
    ) -> list[dict[str, Any]]:
        """
        Retorna os primeiros jogadores do ranking Challenger,
        ordenados pela quantidade de League Points.

        Args:
            limit: Quantidade de jogadores retornados.
            queue: Tipo de fila ranqueada.

        Returns:
            Lista com os jogadores ordenados por League Points.
        """

        if limit < 1:
            raise ValueError(
                "A quantidade de jogadores deve ser maior que zero."
            )

        league = self.get_challenger_league(queue=queue)
        entries = league.get("entries", [])

        if not isinstance(entries, list):
            raise RuntimeError(
                "O ranking Challenger não possui uma lista "
                "válida de jogadores."
            )

        valid_entries = [
            entry
            for entry in entries
            if isinstance(entry, dict)
        ]

        sorted_entries = sorted(
            valid_entries,
            key=lambda entry: entry.get("leaguePoints", 0),
            reverse=True,
        )

        return sorted_entries[:limit]

    def _get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        timeout_message: str,
        connection_message: str,
        unexpected_message: str,
    ) -> Any:
        """
        Executa uma requisição GET para a Riot API.

        Aplica um intervalo preventivo entre chamadas e repete
        automaticamente requisições limitadas pela Riot (HTTP 429).
        """

        last_response: requests.Response | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            self._wait_for_request_slot()

            try:
                response = requests.get(
                    url=url,
                    headers=self.headers,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )

                last_response = response
                self._last_request_at = time.monotonic()

                if response.status_code == 429:
                    retry_after = self._get_retry_after_seconds(response)

                    print(
                        "Limite da Riot atingido. "
                        f"Aguardando {retry_after:.1f} segundo(s) "
                        f"antes da tentativa {attempt + 1}..."
                    )

                    if attempt == self.MAX_RETRIES:
                        break

                    time.sleep(retry_after + 0.5)
                    continue

                if response.status_code in {500, 502, 503, 504}:
                    if attempt == self.MAX_RETRIES:
                        self._handle_http_error(response)

                    wait_seconds = min(2 ** (attempt - 1), 10)

                    print(
                        "A Riot API está temporariamente indisponível. "
                        f"Nova tentativa em {wait_seconds} segundo(s)..."
                    )

                    time.sleep(wait_seconds)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as error:
                if attempt == self.MAX_RETRIES:
                    raise RuntimeError(timeout_message) from error

                time.sleep(min(2 ** (attempt - 1), 10))

            except requests.exceptions.ConnectionError as error:
                if attempt == self.MAX_RETRIES:
                    raise RuntimeError(connection_message) from error

                time.sleep(min(2 ** (attempt - 1), 10))

            except requests.exceptions.HTTPError:
                self._handle_http_error(response)

            except requests.exceptions.JSONDecodeError as error:
                raise RuntimeError(
                    "A Riot API retornou uma resposta inválida."
                ) from error

            except requests.exceptions.RequestException as error:
                raise RuntimeError(
                    f"{unexpected_message}: {error}"
                ) from error

        if last_response is not None:
            self._handle_http_error(last_response)

        raise RuntimeError(
            "Não foi possível concluir a requisição após "
            f"{self.MAX_RETRIES} tentativas."
        )

    def _wait_for_request_slot(self) -> None:
        """
        Mantém um intervalo mínimo entre chamadas à Riot API.
        """

        elapsed = time.monotonic() - self._last_request_at
        remaining = self.MIN_REQUEST_INTERVAL_SECONDS - elapsed

        if remaining > 0:
            time.sleep(remaining)

    def _get_retry_after_seconds(
        self,
        response: requests.Response,
    ) -> float:
        """
        Lê o cabeçalho Retry-After ou utiliza um valor seguro.
        """

        retry_after = response.headers.get("Retry-After")

        if retry_after is None:
            return self.DEFAULT_RETRY_AFTER_SECONDS

        try:
            return max(float(retry_after), 1.0)
        except ValueError:
            return self.DEFAULT_RETRY_AFTER_SECONDS

    @staticmethod
    def _handle_http_error(
        response: requests.Response,
    ) -> None:
        """
        Converte os principais códigos HTTP em mensagens mais claras.
        """

        status_messages = {
            400: (
                "A requisição enviada para a Riot API é inválida."
            ),
            401: (
                "A Riot API Key é inválida ou não foi informada."
            ),
            403: (
                "A Riot API Key expirou ou não possui permissão. "
                "Gere uma nova chave no Riot Developer Portal."
            ),
            404: (
                "O recurso solicitado não foi encontrado "
                "na Riot API."
            ),
            429: (
                "Limite de requisições atingido. "
                "Aguarde alguns segundos e tente novamente."
            ),
            500: (
                "A Riot API apresentou um erro interno."
            ),
            502: (
                "A Riot API está temporariamente indisponível."
            ),
            503: (
                "O serviço da Riot API está indisponível."
            ),
            504: (
                "A Riot API demorou muito para responder."
            ),
        }

        message = status_messages.get(
            response.status_code,
            (
                "Erro ao consultar a Riot API. "
                f"Status HTTP: {response.status_code}."
            ),
        )

        retry_after = response.headers.get("Retry-After")

        if response.status_code == 429 and retry_after:
            message = (
                f"{message} Tempo sugerido de espera: "
                f"{retry_after} segundo(s)."
            )

        raise RuntimeError(message)