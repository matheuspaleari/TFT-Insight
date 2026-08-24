"""
Responsável por transformar um CoachContext em um prompt
estruturado para o modelo de linguagem.
"""

from src.coach.models import (
    CoachContext,
    CoachMetric,
)


class CoachPromptBuilder:
    """
    Constrói o prompt utilizado pelo Coach.

    O modelo de linguagem não deve recalcular métricas,
    alterar prioridades ou inventar informações.

    Sua responsabilidade é apenas traduzir o contexto
    estruturado em uma análise natural e útil.
    """

    @classmethod
    def build(
        cls,
        context: CoachContext,
    ) -> str:
        """
        Constrói o prompt completo para geração da resposta.

        Args:
            context:
                Contexto estruturado produzido pelo
                CoachContextBuilder.

        Returns:
            Prompt completo em formato de texto.
        """

        metrics_text = cls._format_metrics(
            context.metrics
        )

        potential_score = (
            f"{context.potential_score:.1f}"
            if context.potential_score is not None
            else "não calculado"
        )

        return (
            cls._build_system_instructions()
            + "\n\n"
            + cls._build_analysis_context(
                context=context,
                potential_score=potential_score,
                metrics_text=metrics_text,
            )
            + "\n\n"
            + cls._build_response_instructions()
        )

    @staticmethod
    def _build_system_instructions() -> str:
        """
        Define o comportamento obrigatório do Coach.
        """

        return """
Você é um coach especializado em Teamfight Tactics.

Seu papel é transformar uma análise estatística já pronta em uma
explicação clara, prática e útil para o jogador.

REGRAS OBRIGATÓRIAS:

1. Não recalcule nenhuma métrica.
2. Não altere a ordem das prioridades.
3. Não invente dados, causas ou comportamentos.
4. Não afirme que o jogador tomou uma decisão específica se os dados
   apenas indicam uma hipótese.
5. Diferencie métricas de resultado de decisões diretamente controláveis.
6. Nunca recomende literalmente "elimine mais jogadores" ou
   "cause mais dano".
7. Para métricas de resultado, explique os fatores que podem influenciá-las.
8. Use apenas os dados, fatores e recomendações fornecidos no contexto.
9. Quando a causa não for comprovada, use expressões como:
   "pode indicar", "é possível que", "uma hipótese é".
10. Seja direto, didático e respeitoso.
11. Escreva em português do Brasil.
12. Não mencione que você é uma IA ou modelo de linguagem.
""".strip()

    @staticmethod
    def _build_analysis_context(
        *,
        context: CoachContext,
        potential_score: str,
        metrics_text: str,
    ) -> str:
        """
        Insere os dados calculados pelo sistema.
        """

        return f"""
CONTEXTO DA ANÁLISE

Score geral:
{context.score:.1f}

Status:
{context.status}

Benchmark utilizado:
{context.benchmark_name}

Partidas analisadas:
{context.matches_analyzed}

Score potencial:
{potential_score}

PRIORIDADES EM ORDEM DE IMPACTO

{metrics_text}
""".strip()

    @staticmethod
    def _build_response_instructions() -> str:
        """
        Define o formato esperado da resposta final.
        """

        return """
FORMATO OBRIGATÓRIO DA RESPOSTA

Responda utilizando exatamente estas seções:

RESUMO GERAL
Escreva um resumo curto sobre o desempenho em relação ao benchmark.

DIAGNÓSTICO PRINCIPAL
Explique a prioridade número 1.
Deixe claro se ela é uma métrica de resultado ou uma decisão controlável.
Explique por que ela possui maior impacto.

PONTOS POSITIVOS
Liste de 1 a 3 aspectos positivos observáveis nos dados.
Caso os dados não permitam identificar pontos positivos concretos,
diga que a amostra ainda não permite concluir isso com segurança.

PLANO PARA AS PRÓXIMAS PARTIDAS
Crie de 3 a 5 ações práticas.
Use somente as recomendações fornecidas no contexto.
Priorize ações relacionadas à prioridade número 1.

O QUE OBSERVAR
Explique quais sinais o jogador deve acompanhar nas próximas partidas
para avaliar se está evoluindo.

LIMITAÇÕES DA ANÁLISE
Explique brevemente que a análise utiliza dados agregados das partidas
e que algumas causas são hipóteses, não fatos diretamente comprovados.

Não inclua títulos diferentes dos definidos acima.
Não use tabelas.
Não crie métricas adicionais.
Não cite números que não estejam no contexto.
""".strip()

    @classmethod
    def _format_metrics(
        cls,
        metrics: tuple[CoachMetric, ...],
    ) -> str:
        """
        Formata todas as métricas prioritárias.
        """

        if not metrics:
            return (
                "Nenhuma prioridade foi disponibilizada "
                "para esta análise."
            )

        return "\n\n".join(
            cls._format_metric(
                metric=metric,
                rank=rank,
            )
            for rank, metric in enumerate(
                metrics,
                start=1,
            )
        )

    @staticmethod
    def _format_metric(
        *,
        metric: CoachMetric,
        rank: int,
    ) -> str:
        """
        Formata uma métrica individual para o prompt.
        """

        drivers = (
            "\n".join(
                f"- {driver}"
                for driver in metric.drivers
            )
            if metric.drivers
            else "- Nenhum fator cadastrado."
        )

        recommendations = (
            "\n".join(
                f"- {recommendation}"
                for recommendation in metric.recommendations
            )
            if metric.recommendations
            else "- Nenhuma recomendação cadastrada."
        )

        return f"""
PRIORIDADE {rank}

Identificador:
{metric.id}

Título:
{metric.title}

Categoria:
{metric.category}

Descrição:
{metric.description}

Valor do jogador:
{metric.player_value:.2f}

Média do benchmark:
{metric.benchmark_value:.2f}

Score da métrica:
{metric.score:.2f}

Peso no modelo:
{metric.weight:.6f}

Impacto potencial:
{metric.impact:.2f}

Fatores relacionados:
{drivers}

Recomendações disponíveis:
{recommendations}
""".strip()