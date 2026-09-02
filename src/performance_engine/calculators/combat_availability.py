from __future__ import annotations

from dataclasses import dataclass

from src.performance_engine.models import Match


@dataclass(frozen=True, slots=True)
class CombatAvailability:
    """
    Resultado da validação de confiabilidade dos dados de combate.
    """

    available: bool
    total_matches: int
    suspicious_matches: int
    suspicious_ratio: float
    reason: str = ""


class CombatAvailabilityChecker:
    """
    Detecta falha sistêmica nos campos de combate retornados pela fonte.

    Regra V1:
    - exige pelo menos 5 partidas;
    - considera suspeita a partida em que dano == 0 e eliminações == 0;
    - se a proporção suspeita for >= 80%, os dados de combate da amostra
      são considerados indisponíveis.

    Zeros isolados continuam válidos e não são removidos.
    """

    MIN_SAMPLE_SIZE = 5
    SUSPICIOUS_RATIO_THRESHOLD = 0.80

    @classmethod
    def evaluate(
        cls,
        matches: list[Match],
    ) -> CombatAvailability:
        total_matches = len(matches)

        if total_matches == 0:
            return CombatAvailability(
                available=False,
                total_matches=0,
                suspicious_matches=0,
                suspicious_ratio=1.0,
                reason="A amostra não possui partidas.",
            )

        suspicious_matches = sum(
            1
            for match in matches
            if (
                match.total_damage_to_players == 0
                and match.players_eliminated == 0
            )
        )

        suspicious_ratio = (
            suspicious_matches / total_matches
        )

        if total_matches < cls.MIN_SAMPLE_SIZE:
            return CombatAvailability(
                available=True,
                total_matches=total_matches,
                suspicious_matches=suspicious_matches,
                suspicious_ratio=suspicious_ratio,
                reason=(
                    "Amostra pequena demais para declarar falha sistêmica "
                    "nos dados de combate."
                ),
            )

        if suspicious_ratio >= cls.SUSPICIOUS_RATIO_THRESHOLD:
            return CombatAvailability(
                available=False,
                total_matches=total_matches,
                suspicious_matches=suspicious_matches,
                suspicious_ratio=suspicious_ratio,
                reason=(
                    "Os campos de dano e eliminações vieram zerados em "
                    f"{suspicious_matches}/{total_matches} partidas "
                    f"({suspicious_ratio * 100:.1f}% da amostra)."
                ),
            )

        return CombatAvailability(
            available=True,
            total_matches=total_matches,
            suspicious_matches=suspicious_matches,
            suspicious_ratio=suspicious_ratio,
            reason=(
                "A distribuição de zeros não caracteriza falha sistêmica "
                "nos dados de combate."
            ),
        )
