from enum import Enum


class UnitRole(str, Enum):
    DAMAGE_CARRY = "Carry de dano"
    TANK = "Tank principal"
    SUPPORT = "Suporte"
    HYBRID = "Híbrido"
    UNKNOWN = "Desconhecido"
