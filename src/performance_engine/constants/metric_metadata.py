"""
Metadados das métricas utilizadas pelo Performance Engine.

Este módulo centraliza as informações necessárias para interpretar
cada métrica, incluindo:

- nome amigável;
- descrição;
- categoria;
- fatores que influenciam o resultado;
- recomendações práticas.
"""

from dataclasses import dataclass

from src.performance_engine.models import (
    MetricCategory,
    MetricType,
)


@dataclass(frozen=True, slots=True)
class MetricMetadata:
    """
    Representa os metadados associados a uma métrica de desempenho.

    Attributes:
        title:
            Nome amigável da métrica exibido ao jogador.

        description:
            Explicação objetiva sobre o que a métrica representa.

        category:
            Define como a métrica deve ser interpretada.

            Uma métrica pode representar:

            - uma decisão controlável pelo jogador;
            - um resultado obtido durante as partidas;
            - a consistência do desempenho.

        drivers:
            Fatores que podem influenciar o resultado da métrica.

        recommendations:
            Ações práticas que podem ajudar o jogador a melhorar
            os fatores relacionados à métrica.
    """

    title: str
    description: str
    category: MetricCategory
    drivers: tuple[str, ...]
    recommendations: tuple[str, ...]


METRIC_METADATA: dict[MetricType, MetricMetadata] = {
    MetricType.LEVEL: MetricMetadata(
        title="Nível alcançado",
        description=(
            "Avalia o nível médio alcançado pelo jogador durante "
            "as partidas."
        ),
        category=MetricCategory.DECISION,
        drivers=(
            "gestão de ouro",
            "timing de subida de nível",
            "frequência de rerolls",
            "necessidade de estabilizar o tabuleiro",
        ),
        recommendations=(
            (
                "Planeje antecipadamente quando utilizar ouro "
                "para subir de nível."
            ),
            (
                "Equilibre a evolução do nível com a necessidade "
                "de fortalecer o tabuleiro."
            ),
            (
                "Evite realizar rerolls sem considerar o custo "
                "de perder progressão."
            ),
        ),
    ),

    MetricType.DAMAGE_TO_PLAYERS: MetricMetadata(
        title="Dano aos jogadores",
        description=(
            "Avalia o dano médio causado aos adversários ao longo "
            "das partidas. Essa é uma métrica de resultado, "
            "influenciada principalmente pela força do tabuleiro "
            "e pela capacidade de vencer rodadas."
        ),
        category=MetricCategory.RESULT,
        drivers=(
            "força do tabuleiro",
            "qualidade e distribuição dos itens",
            "posicionamento das unidades",
            "timing dos picos de poder",
            "capacidade de preservar sequências de vitória",
        ),
        recommendations=(
            (
                "Fortaleça o tabuleiro nos estágios intermediários "
                "da partida."
            ),
            (
                "Adapte o posicionamento das unidades contra os "
                "principais adversários."
            ),
            (
                "Evite manter componentes sem uso por muitas rodadas."
            ),
            (
                "Identifique os momentos em que gastar ouro pode "
                "preservar uma sequência de vitórias."
            ),
        ),
    ),

    MetricType.PLAYERS_ELIMINATED: MetricMetadata(
        title="Eliminação de jogadores",
        description=(
            "Avalia quantos adversários o jogador elimina, em média, "
            "durante suas partidas. Essa é uma métrica de resultado, "
            "influenciada pela capacidade de construir, fortalecer "
            "e manter um tabuleiro competitivo."
        ),
        category=MetricCategory.RESULT,
        drivers=(
            "força do tabuleiro",
            "gestão de economia",
            "timing de subida de nível",
            "timing de reroll",
            "qualidade e distribuição dos itens",
            "posicionamento das unidades",
            "capacidade de converter vantagem em pressão",
        ),
        recommendations=(
            (
                "Identifique os momentos corretos para investir ouro "
                "e aumentar a força do tabuleiro."
            ),
            (
                "Evite economizar excessivamente quando sua composição "
                "não estiver estável."
            ),
            (
                "Converta vantagens de vida e economia em picos de força "
                "antes que os adversários consigam estabilizar."
            ),
            (
                "Observe os adversários mais vulneráveis e adapte seu "
                "posicionamento para os próximos confrontos."
            ),
        ),
    ),
}


def get_metric_metadata(
    metric_type: MetricType,
) -> MetricMetadata:
    """
    Retorna os metadados associados a uma métrica.

    Args:
        metric_type:
            Tipo da métrica que será consultada.

    Returns:
        Os metadados cadastrados para a métrica.

    Raises:
        ValueError:
            Quando não existem metadados cadastrados para a métrica.
    """

    metadata = METRIC_METADATA.get(metric_type)

    if metadata is None:
        raise ValueError(
            "Metadados não encontrados para a métrica: "
            f"{metric_type.value}"
        )

    return metadata