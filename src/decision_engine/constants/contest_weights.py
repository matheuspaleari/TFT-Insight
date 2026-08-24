"""
Pesos utilizados no cálculo híbrido de contestação.
"""

UNIT_OVERLAP_WEIGHT = 0.50
TRAIT_OVERLAP_WEIGHT = 0.30
CARRY_CONTEST_WEIGHT = 0.20

CONTEST_WEIGHTS_TOTAL = (
    UNIT_OVERLAP_WEIGHT
    + TRAIT_OVERLAP_WEIGHT
    + CARRY_CONTEST_WEIGHT
)

if round(CONTEST_WEIGHTS_TOTAL, 10) != 1.0:
    raise RuntimeError(
        "Os pesos de contestação devem somar 1.0."
    )
