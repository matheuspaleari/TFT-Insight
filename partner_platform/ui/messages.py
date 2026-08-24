from __future__ import annotations

import json
from typing import Any

import httpx
import streamlit as st


def _response_detail(
    response: httpx.Response,
) -> str:
    try:
        payload: Any = response.json()
    except Exception:
        return response.text.strip()

    if isinstance(payload, dict):
        detail = payload.get("detail")

        if isinstance(detail, str):
            return detail

        if detail is not None:
            return json.dumps(
                detail,
                ensure_ascii=False,
            )

    return str(payload)


def friendly_error(
    title: str,
    message: str,
    *,
    hint: str | None = None,
) -> None:
    st.error(
        f"**{title}**\n\n{message}"
    )

    if hint:
        st.caption(
            f"💡 {hint}"
        )


def friendly_exception(
    error: Exception,
    *,
    context: str = "operação",
) -> None:
    """
    Converte erros técnicos em mensagens de produto.

    Detalhes técnicos não são exibidos ao jogador na interface principal.
    """
    status_code: int | None = None
    raw_detail = str(error).strip()

    if isinstance(
        error,
        httpx.HTTPStatusError,
    ):
        status_code = (
            error.response.status_code
        )
        raw_detail = (
            _response_detail(
                error.response
            )
            or raw_detail
        )

    lowered = raw_detail.lower()

    if (
        status_code == 404
        or "player not found" in lowered
        or "jogador não encontrado" in lowered
    ):
        friendly_error(
            "Jogador não encontrado",
            (
                "Não conseguimos localizar esse Riot ID. "
                "Confira o nome e a tag antes de tentar novamente."
            ),
            hint=(
                "Digite a tag sem #. Exemplo: "
                "Pinador doss / 000."
            ),
        )
        return

    if isinstance(
        error,
        (
            httpx.ConnectError,
            httpx.NetworkError,
        ),
    ) or any(
        token in lowered
        for token in (
            "connection refused",
            "winerror 10061",
            "falha de transporte",
        )
    ):
        friendly_error(
            "TFT Insight API indisponível",
            (
                "A plataforma não conseguiu se conectar ao serviço "
                "de análise."
            ),
            hint=(
                "Confirme se `python run_api.py` está ativo "
                "em outro terminal."
            ),
        )
        return

    if status_code in {401, 403}:
        friendly_error(
            "Credencial não autorizada",
            (
                "A API Key atual não possui acesso a esta operação."
            ),
            hint=(
                "Revise a API Key configurada na barra lateral."
            ),
        )
        return

    if status_code == 422:
        friendly_error(
            "Não foi possível processar esses dados",
            raw_detail
            or (
                "A API recebeu a solicitação, mas não conseguiu "
                "validar os dados informados."
            ),
            hint=(
                "Confira Riot ID, tag e quantidade de partidas."
            ),
        )
        return

    if status_code == 429:
        friendly_error(
            "Limite temporário de requisições",
            (
                "A origem de dados está ocupada no momento. "
                "Aguarde alguns segundos e tente novamente."
            ),
        )
        return

    if isinstance(
        error,
        httpx.TimeoutException,
    ) or "timeout" in lowered:
        friendly_error(
            "A análise demorou mais que o esperado",
            (
                "O processamento não terminou dentro do tempo limite."
            ),
            hint=(
                "Tente novamente ou reduza a quantidade de partidas."
            ),
        )
        return

    if status_code in {500, 502, 503, 504}:
        friendly_error(
            "Serviço temporariamente indisponível",
            (
                "A API respondeu, mas não conseguiu concluir a análise "
                "neste momento."
            ),
            hint=(
                "Tente novamente em alguns segundos. Se persistir, "
                "reinicie `python run_api.py` e consulte os logs da API."
            ),
        )
        return

    friendly_error(
        "Não foi possível concluir",
        (
            f"Ocorreu um problema durante {context}. "
            "O restante da plataforma continua disponível."
        ),
        hint="Tente novamente. Se o problema persistir, consulte os logs da API.",
    )
