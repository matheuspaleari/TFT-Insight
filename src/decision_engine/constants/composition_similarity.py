"""
Configuração da similaridade entre identidades de composição.
"""

CARRY_SIMILARITY_WEIGHT = 0.25
TRAIT_SIMILARITY_WEIGHT = 0.50
UNIT_SIMILARITY_WEIGHT = 0.25

COMPOSITION_CLUSTER_THRESHOLD = 55.0

if round(
    CARRY_SIMILARITY_WEIGHT
    + TRAIT_SIMILARITY_WEIGHT
    + UNIT_SIMILARITY_WEIGHT,
    10,
) != 1.0:
    raise RuntimeError(
        "Os pesos de similaridade devem somar 1.0."
    )
