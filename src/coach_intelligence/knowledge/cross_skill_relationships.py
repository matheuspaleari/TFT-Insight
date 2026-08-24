from __future__ import annotations

# Relações pedagógicas candidatas. Elas orientam comparação de sinais,
# mas NÃO representam causalidade.
CROSS_SKILL_RELATIONSHIPS = (
    {
        "id": "leveling_to_board_pressure",
        "source": "leveling",
        "target": "board_pressure",
        "description": (
            "Progressão de nível e pressão de tabuleiro podem se mover "
            "juntas porque níveis alteram o espaço disponível no board."
        ),
    },
    {
        "id": "consistency_to_board_pressure",
        "source": "consistency",
        "target": "board_pressure",
        "description": (
            "Oscilação de resultados pode coexistir com variação na "
            "capacidade de pressionar o lobby."
        ),
    },
)
