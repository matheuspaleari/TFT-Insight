"""
Perfil agregado de uma composição utilizada pelo jogador.
"""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CompositionProfile:
    """
    Consolida frequência e resultados de uma composição.
    """

    composition_key: str
    carry_character_id: str

    matches_played: int
    usage_rate: float

    average_placement: float
    top4_rate: float
    win_rate: float

    average_contest_score: float | None = None

    def __post_init__(self) -> None:
        if not self.composition_key.strip():
            raise ValueError(
                "CompositionProfile.composition_key não pode ser vazio."
            )

        if self.matches_played < 1:
            raise ValueError(
                "CompositionProfile.matches_played deve ser maior que zero."
            )

        for field_name, value in (
            ("usage_rate", self.usage_rate),
            ("top4_rate", self.top4_rate),
            ("win_rate", self.win_rate),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} deve estar entre 0 e 100."
                )

        if not 1.0 <= self.average_placement <= 8.0:
            raise ValueError(
                "average_placement deve estar entre 1 e 8."
            )

        if (
            self.average_contest_score is not None
            and not 0.0 <= self.average_contest_score <= 100.0
        ):
            raise ValueError(
                "average_contest_score deve estar entre 0 e 100."
            )
