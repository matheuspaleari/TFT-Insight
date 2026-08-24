from enum import IntEnum


class SkillLevel(IntEnum):
    """
    Representa o nível estimado de domínio de uma Skill.
    """

    NOT_EVALUATED = 0
    BEGINNER = 1
    DEVELOPING = 2
    COMPETENT = 3
    ADVANCED = 4
    MASTERED = 5