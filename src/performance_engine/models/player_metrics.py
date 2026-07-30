from dataclasses import dataclass

from .combat_metrics import CombatMetrics
from .consistency_metrics import ConsistencyMetrics
from .economy_metrics import EconomyMetrics
from .general_metrics import GeneralMetrics


@dataclass(slots=True, frozen=True)
class PlayerMetrics:
    """
    Porta de entrada oficial do Performance Engine.

    Reúne métricas já calculadas e não conhece a origem dos dados.
    """

    general: GeneralMetrics
    consistency: ConsistencyMetrics
    combat: CombatMetrics
    economy: EconomyMetrics