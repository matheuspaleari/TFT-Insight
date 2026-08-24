from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AugmentSnapshot:
    """Representa um augment informado no resultado final da partida."""

    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "AugmentSnapshot.name não pode ser vazio."
            )
