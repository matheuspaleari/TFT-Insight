from src.learning.models import Skill


ECONOMY = Skill(
    id="economy",
    title="Economia",
    description=(
        "Capacidade de administrar ouro e decidir quando "
        "economizar ou investir em força."
    ),
    related_metric_ids=(
        "average_level",
        "average_damage_to_players",
    ),
)

LEVELING = Skill(
    id="leveling",
    title="Leveling",
    description=(
        "Capacidade de escolher os momentos corretos para "
        "subir de nível sem comprometer a estabilidade."
    ),
    prerequisite_ids=(
        "economy",
    ),
    related_metric_ids=(
        "average_level",
    ),
)

BOARD_PRESSURE = Skill(
    id="board_pressure",
    title="Pressão de tabuleiro",
    description=(
        "Capacidade de construir força suficiente para vencer "
        "rodadas e pressionar os adversários."
    ),
    prerequisite_ids=(
        "economy",
        "leveling",
    ),
    related_metric_ids=(
        "average_damage_to_players",
        "average_players_eliminated",
    ),
)

CONSISTENCY = Skill(
    id="consistency",
    title="Consistência",
    description=(
        "Capacidade de repetir decisões eficientes e reduzir "
        "oscilações entre partidas."
    ),
    related_metric_ids=(
        "placement_standard_deviation",
    ),
)


SKILL_CATALOG: dict[str, Skill] = {
    skill.id: skill
    for skill in (
        ECONOMY,
        LEVELING,
        BOARD_PRESSURE,
        CONSISTENCY,
    )
}


def get_skill(skill_id: str) -> Skill:
    normalized_id = skill_id.strip().lower()

    skill = SKILL_CATALOG.get(normalized_id)

    if skill is None:
        raise ValueError(
            f"Skill não encontrada: {skill_id}"
        )

    return skill


def list_skills() -> tuple[Skill, ...]:
    return tuple(SKILL_CATALOG.values())