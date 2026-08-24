"""
Cliente determinístico utilizado para validar o Coach Engine
sem depender de um modelo de linguagem.
"""

from src.coach.models import (
    CoachContext,
    CoachResponse,
    TrainingPlan,
)


class FakeCoachClient:
    """
    Produz uma resposta previsível utilizando apenas o contexto
    e o plano de treinamento já construído pelo TFT Insight.

    Não consulta IA e não altera o plano recebido.
    """

    def generate(
        self,
        *,
        context: CoachContext,
        prompt: str,
        training_plan: TrainingPlan,
    ) -> CoachResponse:
        """
        Gera uma resposta estruturada baseada no contexto
        e no plano de treinamento.

        Args:
            context:
                Contexto estatístico preparado para o Coach.

            prompt:
                Prompt produzido para um futuro modelo de linguagem.

            training_plan:
                Plano de evolução criado pelo TrainingPlanBuilder.

        Returns:
            Resposta final estruturada do Coach.
        """

        del prompt

        return CoachResponse(
            summary=self._build_summary(
                context=context,
                training_plan=training_plan,
            ),
            training_plan=training_plan,
            raw_text=None,
        )

    @staticmethod
    def _build_summary(
        *,
        context: CoachContext,
        training_plan: TrainingPlan,
    ) -> str:
        """
        Cria um resumo determinístico da sessão de treinamento.
        """

        potential_score_text = (
            f" O score potencial estimado é "
            f"{context.potential_score:.1f}."
            if context.potential_score is not None
            else ""
        )

        return (
            f"A análise considerou {context.matches_analyzed} partidas "
            f"e comparou o jogador ao benchmark "
            f"{context.benchmark_name}. "
            f"O score geral foi {context.score:.1f}, "
            f"com status {context.status}. "
            f"O foco das próximas "
            f"{training_plan.games_target} partidas será "
            f"{training_plan.focus_title.lower()}."
            f"{potential_score_text}"
        )