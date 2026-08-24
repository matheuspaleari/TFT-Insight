from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class BenchmarkMetric:
    """
    Representa a distribuição estatística de uma métrica
    dentro de um benchmark.
    """

    mean: float
    median: float
    standard_deviation: float
    first_quartile: float
    third_quartile: float
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        if self.standard_deviation < 0:
            raise ValueError(
                "O desvio padrão não pode ser negativo."
            )

        if self.minimum > self.maximum:
            raise ValueError(
                "O valor mínimo não pode ser maior "
                "que o valor máximo."
            )

        if not (
            self.minimum
            <= self.first_quartile
            <= self.median
            <= self.third_quartile
            <= self.maximum
        ):
            raise ValueError(
                "Os valores estatísticos estão fora "
                "da ordem esperada."
            )

    def to_dict(self) -> dict[str, float]:
        """
        Converte a métrica em um dicionário serializável.
        """

        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "BenchmarkMetric":
        """
        Reconstrói uma BenchmarkMetric a partir de um dicionário.
        """

        required_fields = {
            "mean",
            "median",
            "standard_deviation",
            "first_quartile",
            "third_quartile",
            "minimum",
            "maximum",
        }

        missing_fields = required_fields - data.keys()

        if missing_fields:
            raise ValueError(
                "Campos ausentes em BenchmarkMetric: "
                + ", ".join(sorted(missing_fields))
            )

        return cls(
            mean=float(data["mean"]),
            median=float(data["median"]),
            standard_deviation=float(
                data["standard_deviation"]
            ),
            first_quartile=float(
                data["first_quartile"]
            ),
            third_quartile=float(
                data["third_quartile"]
            ),
            minimum=float(data["minimum"]),
            maximum=float(data["maximum"]),
        )