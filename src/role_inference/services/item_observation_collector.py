from collections import defaultdict
from dataclasses import replace

from src.performance_engine.models import Match
from src.role_inference.models import (
    ItemClassification,
    ItemObservation,
    UnitRoleSeed,
)

from .unit_role_seed_inference import (
    UnitRoleSeedInference,
)


class ItemObservationCollector:
    """
    Gera observações estatísticas a partir de partidas enriquecidas.

    Como o histórico oficial não expõe posição no tabuleiro, esta versão
    não inventa frontline/backline. Esses campos permanecem zerados.

    O papel inicial da unidade é inferido apenas quando sua itemização
    possui evidência suficiente nos metadados completos.
    """

    @classmethod
    def collect(
        cls,
        *,
        matches: list[Match],
        item_classifications: dict[
            str,
            ItemClassification,
        ],
        existing: dict[
            str,
            ItemObservation,
        ] | None = None,
    ) -> dict[str, ItemObservation]:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        counters = defaultdict(
            lambda: {
                "damage_carry_uses": 0,
                "tank_uses": 0,
                "support_uses": 0,
            }
        )

        for match in matches:
            for participant in match.participants:
                for unit in participant.units:
                    assessment = (
                        UnitRoleSeedInference.infer(
                            unit=unit,
                            classifications=(
                                item_classifications
                            ),
                        )
                    )

                    for item_id in unit.items:
                        if (
                            assessment.role
                            == UnitRoleSeed.DAMAGE_CARRY
                        ):
                            counters[item_id][
                                "damage_carry_uses"
                            ] += 1

                        elif (
                            assessment.role
                            == UnitRoleSeed.TANK
                        ):
                            counters[item_id][
                                "tank_uses"
                            ] += 1

                        elif (
                            assessment.role
                            == UnitRoleSeed.SUPPORT
                        ):
                            counters[item_id][
                                "support_uses"
                            ] += 1

        observations = dict(
            existing
            or {}
        )

        for item_id, values in counters.items():
            current = observations.get(
                item_id,
                ItemObservation(
                    item_id=item_id
                ),
            )

            observations[item_id] = replace(
                current,
                damage_carry_uses=(
                    current.damage_carry_uses
                    + values["damage_carry_uses"]
                ),
                tank_uses=(
                    current.tank_uses
                    + values["tank_uses"]
                ),
                support_uses=(
                    current.support_uses
                    + values["support_uses"]
                ),
            )

        return observations
