from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from ._compatibility import validate_contract_version
from ._transport import (
    ClientOptions,
    request_with_retries,
)
from .exceptions import ResponseValidationError
from .models import (
    AnalysisSignals,
    AnalyzeResponse,
    CapabilitiesResponse,
    HealthResponse,
    IntegratedAnalysisResponse,
)
from .version import __version__


class TFTInsightClient:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8000",
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.options = ClientOptions(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            user_agent=f"tft-insight-python/{__version__}",
        )

        self._client = httpx.Client(
            base_url=self.options.base_url,
            timeout=self.options.timeout,
            transport=transport,
        )

    def __enter__(self) -> "TFTInsightClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def health(self) -> HealthResponse:
        return self._get(
            "/health",
            HealthResponse,
        )

    def capabilities(self) -> CapabilitiesResponse:
        return self._get(
            "/v1/capabilities",
            CapabilitiesResponse,
        )

    def analyze_signals(
        self,
        *,
        signals: AnalysisSignals | dict[str, Any],
        source: str = "partner",
        game_name: str | None = None,
        tag_line: str | None = None,
        puuid: str | None = None,
        region: str = "BR1",
        patch: str | None = None,
        set_number: int | None = None,
        request_id: str | None = None,
    ) -> AnalyzeResponse:
        parsed_signals = (
            signals
            if isinstance(signals, AnalysisSignals)
            else AnalysisSignals.model_validate(signals)
        )

        player = None

        if puuid or (game_name and tag_line):
            player = {
                "puuid": puuid,
                "game_name": game_name,
                "tag_line": tag_line,
                "region": region,
            }

        payload = {
            "request_id": request_id,
            "source": source,
            "player": player,
            "patch": patch,
            "set_number": set_number,
            "signals": parsed_signals.model_dump(
                mode="json"
            ),
        }

        response = self._post(
            "/v1/analyze",
            payload,
            AnalyzeResponse,
            request_id=request_id,
        )

        validate_contract_version(
            response.meta.contract_version
        )

        return response

    def analyze_player(
        self,
        *,
        game_name: str | None = None,
        tag_line: str | None = None,
        puuid: str | None = None,
        region: str = "BR1",
        match_count: int = 20,
        learn: bool = True,
        source: str = "partner",
        request_id: str | None = None,
    ) -> IntegratedAnalysisResponse:
        payload = {
            "request_id": request_id,
            "source": source,
            "player": {
                "puuid": puuid,
                "game_name": game_name,
                "tag_line": tag_line,
                "region": region,
            },
            "match_count": match_count,
            "learn": learn,
        }

        response = self._post(
            "/v1/analyze/player",
            payload,
            IntegratedAnalysisResponse,
            request_id=request_id,
        )

        validate_contract_version(
            response.analysis.meta.contract_version
        )

        return response

    def analyze_match(
        self,
        *,
        puuid: str,
        match_data: dict[str, Any],
        learn: bool = False,
        source: str = "partner",
        request_id: str | None = None,
    ) -> IntegratedAnalysisResponse:
        payload = {
            "request_id": request_id,
            "source": source,
            "puuid": puuid,
            "match_data": match_data,
            "learn": learn,
        }

        response = self._post(
            "/v1/analyze/match",
            payload,
            IntegratedAnalysisResponse,
            request_id=request_id,
        )

        validate_contract_version(
            response.analysis.meta.contract_version
        )

        return response

    def _get(self, path: str, model_type):
        response = request_with_retries(
            self._client,
            method="GET",
            url=path,
            options=self.options,
        )

        return self._validate_response(
            response,
            model_type,
        )

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        model_type,
        *,
        request_id: str | None,
    ):
        resolved_request_id = (
            request_id or str(uuid4())
        )

        response = request_with_retries(
            self._client,
            method="POST",
            url=path,
            options=self.options,
            json_data=payload,
            request_id=resolved_request_id,
        )

        return self._validate_response(
            response,
            model_type,
        )

    @staticmethod
    def _validate_response(
        response: httpx.Response,
        model_type,
    ):
        try:
            return model_type.model_validate(
                response.json()
            )
        except (
            ValueError,
            ValidationError,
        ) as error:
            raise ResponseValidationError(
                "A resposta da API não segue "
                f"o contrato {model_type.__name__}."
            ) from error
