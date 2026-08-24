"""
Serviço responsável por enriquecer as prioridades de desempenho
com descrições e recomendações práticas.
"""

from src.performance_engine.constants.metric_metadata import (
    MetricMetadata,
    get_metric_metadata,
)
from src.performance_engine.models import (
    MetricCategory,
    MetricType,
    Performance,
    Priority,
)


class RecommendationService:
    """
    Enriquece as prioridades de uma performance com informações
    interpretativas e recomendações práticas.

    O serviço diferencia métricas diretamente controláveis pelo jogador
    de métricas que representam resultados obtidos durante as partidas.
    """

    @classmethod
    def apply(
        cls,
        performance: Performance,
    ) -> Performance:
        """
        Adiciona descrições e recomendações às prioridades.

        Args:
            performance:
                Performance que contém as prioridades calculadas.

        Returns:
            A própria performance, enriquecida com descrições
            e recomendações.
        """

        for priority in performance.priorities:
            metric_type = MetricType(priority.id)

            metadata = get_metric_metadata(metric_type)

            priority.description = cls._build_description(
                priority=priority,
                metadata=metadata,
            )

            priority.recommendations = cls._build_recommendations(
                metadata=metadata,
            )

        return performance

    @classmethod
    def _build_description(
        cls,
        priority: Priority,
        metadata: MetricMetadata,
    ) -> str:
        """
        Monta a descrição de acordo com a categoria da métrica.
        """

        if metadata.category == MetricCategory.RESULT:
            return cls._build_result_description(
                priority=priority,
                metadata=metadata,
            )

        if metadata.category == MetricCategory.DECISION:
            return cls._build_decision_description(
                priority=priority,
                metadata=metadata,
            )

        if metadata.category == MetricCategory.CONSISTENCY:
            return cls._build_consistency_description(
                priority=priority,
                metadata=metadata,
            )

        raise ValueError(
            "Categoria de métrica desconhecida: "
            f"{metadata.category}"
        )

    @classmethod
    def _build_result_description(
        cls,
        priority: Priority,
        metadata: MetricMetadata,
    ) -> str:
        """
        Cria a descrição de uma métrica que representa um resultado.

        Métricas de resultado não são ações executadas diretamente
        pelo jogador. Elas são consequências de outras decisões.
        """

        drivers = cls._format_drivers(metadata.drivers)

        return (
            f"{metadata.description}\n\n"
            f"Esta foi sua oportunidade de melhoria número "
            f"{priority.rank}.\n\n"
            "Essa métrica representa um resultado obtido ao longo da "
            "partida, e não uma ação executada diretamente pelo jogador.\n\n"
            "Ela normalmente é consequência de decisões relacionadas a:\n\n"
            f"{drivers}\n\n"
            "Melhorar esses fatores tende a elevar naturalmente essa "
            "métrica e aumentar seu desempenho geral."
        )

    @classmethod
    def _build_decision_description(
        cls,
        priority: Priority,
        metadata: MetricMetadata,
    ) -> str:
        """
        Cria a descrição de uma métrica diretamente relacionada
        às decisões do jogador.
        """

        drivers = cls._format_drivers(metadata.drivers)

        return (
            f"{metadata.description}\n\n"
            f"Esta foi sua oportunidade de melhoria número "
            f"{priority.rank}.\n\n"
            "Essa métrica está diretamente relacionada às decisões "
            "tomadas pelo jogador durante a partida.\n\n"
            "Os principais fatores envolvidos são:\n\n"
            f"{drivers}\n\n"
            "Pequenos ajustes nesses aspectos podem produzir ganhos "
            "consistentes no desempenho geral."
        )

    @classmethod
    def _build_consistency_description(
        cls,
        priority: Priority,
        metadata: MetricMetadata,
    ) -> str:
        """
        Cria a descrição de uma métrica relacionada à estabilidade
        do desempenho entre partidas.
        """

        drivers = cls._format_drivers(metadata.drivers)

        return (
            f"{metadata.description}\n\n"
            f"Esta foi sua oportunidade de melhoria número "
            f"{priority.rank}.\n\n"
            "Essa métrica representa a estabilidade do desempenho "
            "do jogador entre diferentes partidas.\n\n"
            "Ela costuma ser influenciada por:\n\n"
            f"{drivers}\n\n"
            "Melhorar esses fatores pode reduzir oscilações e tornar "
            "os resultados mais consistentes."
        )

    @staticmethod
    def _format_drivers(
        drivers: tuple[str, ...],
    ) -> str:
        """
        Formata os fatores de influência como uma lista legível.
        """

        if not drivers:
            return "• Nenhum fator de influência cadastrado."

        return "\n".join(
            f"• {driver.capitalize()}"
            for driver in drivers
        )

    @staticmethod
    def _build_recommendations(
        metadata: MetricMetadata,
    ) -> list[str]:
        """
        Converte as recomendações imutáveis dos metadados
        em uma lista que pode ser associada à prioridade.
        """

        return list(metadata.recommendations)