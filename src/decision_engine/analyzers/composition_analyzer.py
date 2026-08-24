from src.decision_engine.models import CompositionSnapshot
from src.performance_engine.models import Match
from src.role_inference.models import ItemClassification

from .composition_identity_analyzer import (
    CompositionIdentityAnalyzer,
)


class CompositionAnalyzer:
    @classmethod
    def analyze(
        cls,
        match: Match,
        *,
        item_classifications: dict[
            str,
            ItemClassification,
        ] | None = None,
    ) -> CompositionSnapshot:
        player = match.analyzed_participant

        if player is None:
            raise ValueError(
                "O Match não possui participante analisado."
            )

        identity = CompositionIdentityAnalyzer.analyze(
            player,
            item_classifications=item_classifications,
        )

        return CompositionSnapshot(
            match_id=match.match_id,
            placement=match.placement,
            carry_character_id=identity.carry_character_id,
            tank_character_id=identity.tank_character_id,
            support_character_id=identity.support_character_id,
            unit_ids=identity.core_unit_ids,
            trait_names=identity.primary_trait_names,
            composition_key=identity.identity_key,
        )
