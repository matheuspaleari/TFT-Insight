from dataclasses import dataclass, field


@dataclass(slots=True)
class Priority:
    """
    Representa uma oportunidade de melhoria identificada
    pelo Performance Engine.

    Responsabilidade:
        Transportar informações sobre uma prioridade de melhoria.

    Entrada:
        Dados calculados pelo RecommendationEngine.

    Saída:
        Objeto estruturado utilizado pela Home, Dashboard e Coach AI.

    Este módulo:
        - Não calcula métricas.
        - Não conhece Streamlit.
        - Não acessa a Riot API.
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

    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Priority.id não pode ser vazio.")

        if not self.title.strip():
            raise ValueError("Priority.title não pode ser vazio.")

        if self.rank < 1:
            raise ValueError("Priority.rank deve ser maior ou igual a 1.")

        self.current_score = self._normalize_score(self.current_score)
        self.benchmark_score = self._normalize_score(self.benchmark_score)
        self.confidence = self._normalize_score(self.confidence)

        self.gap = round(float(self.gap), 2)
        self.impact = round(float(self.impact), 2)

    @staticmethod
    def _normalize_score(value: float) -> float:
        """
        Mantém valores percentuais entre 0 e 100.

        Essa validação protege o modelo, mas não representa
        uma regra de negócio do Performance Engine.
        """
        return round(max(0.0, min(100.0, float(value))), 2)