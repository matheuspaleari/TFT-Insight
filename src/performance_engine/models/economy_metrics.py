from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EconomyMetrics:
    """
    Métricas econômicas diretamente observáveis.

    Esta classe não interpreta se guardar ouro foi uma decisão boa ou ruim.
    """

    average_gold_left: float | None = None

    def __post_init__(self) -> None:
        if self.average_gold_left is not None:
            if self.average_gold_left < 0:
                raise ValueError(
                    "average_gold_left não pode ser negativo."
                )