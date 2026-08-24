from .exceptions import ContractCompatibilityError
from .version import SUPPORTED_CONTRACT_MAJOR


def validate_contract_version(
    contract_version: str,
) -> None:
    try:
        major = int(contract_version.split(".", 1)[0])
    except (ValueError, AttributeError, IndexError) as error:
        raise ContractCompatibilityError(
            "A API retornou uma versão de contrato inválida: "
            f"{contract_version!r}."
        ) from error

    if major != SUPPORTED_CONTRACT_MAJOR:
        raise ContractCompatibilityError(
            "Contrato incompatível. "
            f"SDK suporta major {SUPPORTED_CONTRACT_MAJOR}, "
            f"API retornou {contract_version}."
        )
