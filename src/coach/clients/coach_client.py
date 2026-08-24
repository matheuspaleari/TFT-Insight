"""
Contrato dos clientes responsáveis por gerar a resposta do Coach.
"""

from typing import Protocol

from src.coach.models import (
    CoachContext,
    CoachResponse,
    TrainingPlan,
)


class CoachClient(Protocol):
    """
    Define o contrato que qualquer cliente de geração deve seguir.

    O cliente não calcula o plano de treinamento. Ele recebe
    toda a estrutura pronta e apenas produz a resposta final.
    """

    def generate(
        self,
        *,
        context: CoachContext,
        prompt: str,
        training_plan: TrainingPlan,
    ) -> CoachResponse:
        """
        Gera uma resposta usando o contexto, o prompt
        e o plano de treinamento já definido.
        """
        ...