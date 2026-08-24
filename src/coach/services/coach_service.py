"""
Serviço principal do Coach Engine.

Coordena a transformação da Performance em contexto,
a criação do plano de treinamento, a construção do prompt
e a geração da resposta final.
"""

from src.coach.builders import (
    CoachContextBuilder,
    CoachPromptBuilder,
    TrainingPlanBuilder,
)
from src.coach.clients import (
    CoachClient,
    FakeCoachClient,
)
from src.coach.models import CoachResponse
from src.performance_engine.models import Performance


class CoachService:
    """
    Orquestra o fluxo completo do Coach.

    Este serviço não calcula métricas e não altera prioridades.
    Ele transforma a análise existente em uma sessão estruturada
    de treinamento.
    """

    def __init__(
        self,
        client: CoachClient | None = None,
    ) -> None:
        self.client = client or FakeCoachClient()

    def generate(
        self,
        *,
        performance: Performance,
    ) -> CoachResponse:
        """
        Gera a resposta do Coach a partir de uma Performance.

        Fluxo:

            Performance
                ↓
            CoachContext
                ↓
            TrainingPlan
                ↓
            Prompt
                ↓
            CoachClient
                ↓
            CoachResponse
        """

        context = CoachContextBuilder.build(
            performance=performance,
        )

        training_plan = TrainingPlanBuilder.build(
            context=context,
        )

        prompt = CoachPromptBuilder.build(
            context=context,
        )

        return self.client.generate(
            context=context,
            prompt=prompt,
            training_plan=training_plan,
        )