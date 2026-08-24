from __future__ import annotations

from typing import Any


class TFTInsightError(Exception):
    """Erro base do SDK."""


class ConfigurationError(TFTInsightError):
    """Configuração inválida do cliente."""


class TransportError(TFTInsightError):
    """Falha de rede, timeout ou conexão."""


class ContractCompatibilityError(TFTInsightError):
    """Contrato retornado pela API incompatível com o SDK."""


class ResponseValidationError(TFTInsightError):
    """Resposta da API não segue o contrato esperado."""


class TFTInsightAPIError(TFTInsightError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_code: str | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        self.details = details or {}


class AuthenticationError(TFTInsightAPIError):
    """API key inválida ou ausente."""


class AuthorizationError(TFTInsightAPIError):
    """Cliente autenticado sem permissão."""


class NotFoundError(TFTInsightAPIError):
    """Recurso não encontrado."""


class PlayerNotFoundError(NotFoundError):
    """Jogador não encontrado."""


class ValidationAPIError(TFTInsightAPIError):
    """Entrada rejeitada pela API."""


class RateLimitError(TFTInsightAPIError):
    """Limite de requisições atingido."""


class ServerError(TFTInsightAPIError):
    """Erro interno ou indisponibilidade da API."""
