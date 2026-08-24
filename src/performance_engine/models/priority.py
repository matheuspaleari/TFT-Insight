from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Priority:
    """
    Representa uma oportunidade de melhoria identificada
    pelo Performance Engine.
    """

    id: str
    title: str
    description: str

    current_score: float
    benchmark_score: float

    gap: float
    impact: float
    confidence: float

    rank: int

    recommendations: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "Priority.id não pode ser vazio."
            )

        if not self.title.strip():
            raise ValueError(
                "Priority.title não pode ser vazio."
            )

        if self.rank < 1:
            raise ValueError(
                "Priority.rank deve ser maior ou igual a 1."
            )

        self.current_score = self._normalize_score(
            self.current_score
        )

        self.benchmark_score = self._normalize_score(
            self.benchmark_score
        )

        self.confidence = self._normalize_score(
            self.confidence
        )

        self.gap = round(
            float(self.gap),
            2,
        )

        self.impact = round(
            float(self.impact),
            2,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Converte a prioridade em um dicionário serializável.
        """

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "current_score": self.current_score,
            "benchmark_score": self.benchmark_score,
            "gap": self.gap,
            "impact": self.impact,
            "confidence": self.confidence,
            "rank": self.rank,
            "recommendations": list(
                self.recommendations
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Priority":
        """
        Reconstrói uma prioridade a partir de um dicionário.
        """

        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            description=str(data["description"]),
            current_score=float(
                data["current_score"]
            ),
            benchmark_score=float(
                data["benchmark_score"]
            ),
            gap=float(data["gap"]),
            impact=float(data["impact"]),
            confidence=float(
                data["confidence"]
            ),
            rank=int(data["rank"]),
            recommendations=[
                str(item)
                for item in data.get(
                    "recommendations",
                    [],
                )
            ],
        )

    @staticmethod
    def _normalize_score(
        value: float,
    ) -> float:
        """
        Mantém valores percentuais entre 0 e 100.
        """

        return round(
            max(
                0.0,
                min(
                    100.0,
                    float(value),
                ),
            ),
            2,
        )