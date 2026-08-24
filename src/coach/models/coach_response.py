from dataclasses import dataclass

from .training_plan import TrainingPlan


@dataclass(slots=True, frozen=True)
class CoachResponse:
    """
    Representa a resposta final produzida pelo Coach.

    O resumo apresenta uma visão geral da análise.

    O TrainingPlan concentra todo o plano estruturado de evolução,
    incluindo objetivo, ações, checklist, erros comuns, conceitos
    de estudo e métricas que serão acompanhadas.

    O raw_text poderá armazenar futuramente a versão em linguagem
    natural produzida por um modelo local, como o Ollama.
    """

    summary: str
    training_plan: TrainingPlan

    raw_text: str | None = None

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError(
                "CoachResponse.summary não pode ser vazio."
            )

        if self.raw_text is not None:
            normalized_raw_text = self.raw_text.strip()

            object.__setattr__(
                self,
                "raw_text",
                normalized_raw_text or None,
            )