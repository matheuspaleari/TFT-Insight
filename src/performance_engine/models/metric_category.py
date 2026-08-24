"""
Categorias das métricas avaliadas pelo Performance Engine.
"""

from enum import Enum


class MetricCategory(str, Enum):
    """
    Define como uma métrica deve ser interpretada.

    RESULT:
        Representa uma consequência do desempenho do jogador.
        Não deve gerar recomendações literais.

    DECISION:
        Representa uma decisão ou comportamento mais diretamente
        controlável pelo jogador.

    CONSISTENCY:
        Representa a estabilidade dos resultados entre partidas.
    """

    RESULT = "result"
    DECISION = "decision"
    CONSISTENCY = "consistency"