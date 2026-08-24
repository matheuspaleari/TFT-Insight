from enum import Enum


class UnitRoleSeed(str, Enum):
    DAMAGE_CARRY = "damage_carry"
    TANK = "tank"
    SUPPORT = "support"
    UNKNOWN = "unknown"
