from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.integration_engine.services.cached_match_service import CachedMatchService
from src.riot_client import RiotClient


SEPARATOR = "=" * 112
SUB_SEPARATOR = "-" * 112


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = ""

    def json(self) -> object:
        return self._payload

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            error = requests.exceptions.HTTPError(
                f"HTTP {self.status_code}"
            )
            error.response = self
            raise error


def print_case(
    *,
    number: int,
    title: str,
) -> None:
    print()
    print(f"TESTE {number} — {title}")
    print(SUB_SEPARATOR)


def print_result(
    *,
    ok: bool,
    detail: str,
) -> None:
    print(f"Status  : {'OK' if ok else 'ERRO'}")
    print(f"Detalhe : {detail}")


def test_timeout() -> dict:
    """
    Valida que um timeout da Riot não vaza como
    requests.exceptions.Timeout para as camadas superiores.

    O RiotClient deve converter a falha externa em RuntimeError
    controlado, com mensagem compreensível.
    """

    client = RiotClient()

    try:
        with (
            patch(
                "src.riot_client.requests.get",
                side_effect=requests.exceptions.Timeout(
                    "timeout simulado"
                ),
            ),
            patch(
                "src.riot_client.time.sleep",
                return_value=None,
            ),
        ):
            client.get_account(
                game_name="teste",
                tag_line="000",
            )

    except RuntimeError as error:
        message = str(error)

        return {
            "ok": True,
            "detail": (
                "Timeout convertido em RuntimeError controlado: "
                f"{message}"
            ),
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "detail": (
                "requests.exceptions.Timeout escapou do RiotClient."
            ),
        }

    except Exception as error:
        return {
            "ok": False,
            "detail": (
                f"Exceção inesperada: "
                f"{type(error).__name__}: {error}"
            ),
        }

    return {
        "ok": False,
        "detail": (
            "A chamada terminou sem erro mesmo com timeout simulado."
        ),
    }


def test_rate_limit_429() -> dict:
    """
    Primeira chamada recebe HTTP 429.

    A segunda chamada retorna sucesso.

    O objetivo é comprovar que o RiotClient respeita o fluxo
    de retry e consegue se recuperar do rate limit.
    """

    client = RiotClient()

    responses = [
        FakeResponse(
            status_code=429,
            payload={
                "status": {
                    "status_code": 429,
                    "message": "Rate limit exceeded",
                }
            },
            headers={
                "Retry-After": "1",
            },
        ),
        FakeResponse(
            status_code=200,
            payload={
                "puuid": "PUUID_TEST_429",
                "gameName": "teste",
                "tagLine": "000",
            },
        ),
    ]

    calls = 0

    def fake_get(*args, **kwargs):
        nonlocal calls

        index = min(
            calls,
            len(responses) - 1,
        )

        response = responses[index]
        calls += 1

        return response

    try:
        with (
            patch(
                "src.riot_client.requests.get",
                side_effect=fake_get,
            ),
            patch(
                "src.riot_client.time.sleep",
                return_value=None,
            ),
        ):
            account = client.get_account(
                game_name="teste",
                tag_line="000",
            )

        recovered = (
            isinstance(account, dict)
            and account.get("puuid") == "PUUID_TEST_429"
            and calls >= 2
        )

        if recovered:
            return {
                "ok": True,
                "detail": (
                    f"HTTP 429 recuperado com retry. "
                    f"Chamadas HTTP simuladas: {calls}."
                ),
            }

        return {
            "ok": False,
            "detail": (
                "O cliente não recuperou corretamente após o HTTP 429. "
                f"Chamadas: {calls}; retorno: {account!r}"
            ),
        }

    except Exception as error:
        return {
            "ok": False,
            "detail": (
                f"Falha durante recuperação do 429: "
                f"{type(error).__name__}: {error}"
            ),
        }


def test_service_unavailable_503() -> dict:
    """
    Simula indisponibilidade da Riot.

    O comportamento esperado é uma exceção controlada da camada
    RiotClient, e não requests.HTTPError vazando para o restante
    da aplicação.
    """

    client = RiotClient()

    def unavailable(*args, **kwargs):
        return FakeResponse(
            status_code=503,
            payload={
                "status": {
                    "status_code": 503,
                    "message": "Service unavailable",
                }
            },
        )

    try:
        with (
            patch(
                "src.riot_client.requests.get",
                side_effect=unavailable,
            ),
            patch(
                "src.riot_client.time.sleep",
                return_value=None,
            ),
        ):
            client.get_account(
                game_name="teste",
                tag_line="000",
            )

    except RuntimeError as error:
        return {
            "ok": True,
            "detail": (
                "HTTP 503 convertido em RuntimeError controlado: "
                f"{error}"
            ),
        }

    except requests.exceptions.HTTPError as error:
        return {
            "ok": False,
            "detail": (
                "requests.HTTPError escapou do RiotClient: "
                f"{error}"
            ),
        }

    except Exception as error:
        return {
            "ok": False,
            "detail": (
                f"Exceção inesperada: "
                f"{type(error).__name__}: {error}"
            ),
        }

    return {
        "ok": False,
        "detail": (
            "A chamada terminou sem erro mesmo com HTTP 503 simulado."
        ),
    }


class PartialFailureRiotClient:
    """
    RiotClient mínimo para testar o CachedMatchService.

    MATCH_002 falha propositalmente.
    Os demais candidatos continuam disponíveis.
    """

    def get_match_ids(
        self,
        *,
        puuid: str,
        count: int,
    ) -> list[str]:
        return [
            "MATCH_001",
            "MATCH_002",
            "MATCH_003",
        ][:count]

    def get_match_details(
        self,
        *,
        match_id: str,
    ) -> dict:
        if match_id == "MATCH_002":
            raise RuntimeError(
                "Falha simulada ao baixar MATCH_002."
            )

        return {
            "metadata": {
                "match_id": match_id,
            },
            "info": {
                "game_datetime": 0,
            },
            "_diagnostic_match_id": match_id,
        }


class DiagnosticCachedMatchService(CachedMatchService):
    @staticmethod
    def _transform(
        *,
        payload: dict,
        puuid: str,
    ):
        """
        Para este diagnóstico não precisamos validar novamente
        o MatchTransformer.

        O objetivo é isolar exclusivamente o comportamento do loader
        quando uma partida individual falha.
        """
        return {
            "puuid": puuid,
            "match_id": (
                payload.get("metadata", {})
                .get("match_id")
            ),
        }


def test_partial_match_failure() -> dict:
    """
    Solicita duas partidas válidas com três candidatos:

        MATCH_001 -> OK
        MATCH_002 -> ERRO
        MATCH_003 -> OK

    O loader deve ignorar a falha isolada e continuar até conseguir
    as duas partidas válidas solicitadas.
    """

    with tempfile.TemporaryDirectory(
        prefix="tft_insight_roadmap21_"
    ) as temp_dir:

        project_root = Path(temp_dir)

        client = PartialFailureRiotClient()

        service = DiagnosticCachedMatchService(
            project_root=project_root,
            riot_client=client,
        )

        try:
            result = service.load_player_matches_target(
                puuid="PUUID_TEST_PARTIAL",
                target_count=2,
                candidate_count=3,
            )

        except Exception as error:
            return {
                "ok": False,
                "detail": (
                    "Uma falha individual derrubou o loader: "
                    f"{type(error).__name__}: {error}"
                ),
            }

        valid_matches = len(result.matches)

        conditions = {
            "valid_matches": valid_matches == 2,
            "failed_matches": result.failed_matches == 1,
            "downloaded": result.new_matches_downloaded == 2,
            "considered": result.candidate_ids_considered == 3,
        }

        ok = all(
            conditions.values()
        )

        return {
            "ok": ok,
            "detail": (
                f"válidas={valid_matches} | "
                f"falhas={result.failed_matches} | "
                f"downloads={result.new_matches_downloaded} | "
                f"consideradas={result.candidate_ids_considered}"
            ),
            "conditions": conditions,
        }


def main() -> None:
    print()
    print(SEPARATOR)
    print(
        "#33 / ROADMAP 21 - "
        "DIAGNÓSTICO COMPORTAMENTAL DE ERROS + RESILIÊNCIA"
    )
    print(SEPARATOR)

    tests = (
        (
            "TIMEOUT DA RIOT",
            test_timeout,
        ),
        (
            "HTTP 429 / RATE LIMIT + RETRY",
            test_rate_limit_429,
        ),
        (
            "HTTP 503 / INDISPONIBILIDADE",
            test_service_unavailable_503,
        ),
        (
            "FALHA ISOLADA DE PARTIDA",
            test_partial_match_failure,
        ),
    )

    results: list[dict] = []

    for index, (
        title,
        function,
    ) in enumerate(
        tests,
        1,
    ):
        print_case(
            number=index,
            title=title,
        )

        try:
            result = function()

        except Exception as error:
            result = {
                "ok": False,
                "detail": (
                    "O próprio diagnóstico encontrou uma "
                    "exceção inesperada: "
                    f"{type(error).__name__}: {error}"
                ),
            }

        results.append(
            {
                "test": title,
                **result,
            }
        )

        print_result(
            ok=bool(
                result.get("ok")
            ),
            detail=str(
                result.get(
                    "detail",
                    "",
                )
            ),
        )

        conditions = result.get(
            "conditions"
        )

        if isinstance(
            conditions,
            dict,
        ):
            for name, ok in conditions.items():
                print(
                    f"         "
                    f"{name:<16}: "
                    f"{'OK' if ok else 'ERRO'}"
                )

    passed = sum(
        1
        for item in results
        if item.get("ok")
    )

    total = len(
        results
    )

    print()
    print(SEPARATOR)
    print("RESUMO")
    print(SUB_SEPARATOR)

    for item in results:
        print(
            f"{'OK' if item.get('ok') else 'ERRO':<4} | "
            f"{item['test']}"
        )

    print()
    print(
        f"PASSARAM: {passed}/{total}"
    )

    print(SEPARATOR)

    if passed == total:
        print(
            "#33 ERROS + RESILIÊNCIA: "
            "DIAGNÓSTICO COMPORTAMENTAL VALIDADO"
        )

        print()
        print(
            "ROADMAP 21 — PERFORMANCE + CACHE + ERROS: "
            "PRONTA PARA AUDITORIA FINAL"
        )

        return

    print(
        "#33 ERROS + RESILIÊNCIA: REVISAR"
    )

    raise SystemExit(1)


if __name__ == "__main__":
    main()