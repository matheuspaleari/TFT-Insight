"""
Cluster de composições semelhantes.
"""

from dataclasses import dataclass, field

from .composition_snapshot import CompositionSnapshot


@dataclass(slots=True, frozen=True)
class CompositionCluster:
    """
    Agrupa variantes da mesma composição estratégica.
    """

    cluster_id: str
    representative: CompositionSnapshot

    snapshots: tuple[CompositionSnapshot, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.cluster_id.strip():
            raise ValueError(
                "CompositionCluster.cluster_id não pode ser vazio."
            )

        if not self.snapshots:
            raise ValueError(
                "CompositionCluster.snapshots não pode ser vazio."
            )

        if self.representative not in self.snapshots:
            raise ValueError(
                "A composição representativa deve pertencer ao cluster."
            )

    @property
    def matches_played(self) -> int:
        return len(self.snapshots)
