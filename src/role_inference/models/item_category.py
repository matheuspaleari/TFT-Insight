from enum import Enum


class ItemCategory(str, Enum):
    OFFENSE = "Ofensivo"
    DEFENSE = "Defensivo"
    UTILITY = "Utilidade"
    HYBRID = "Híbrido"
    UNKNOWN = "Desconhecido"
