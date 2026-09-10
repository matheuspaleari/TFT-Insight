from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.decision_engine.analyzers.itemization_history_analyzer import (
    ItemizationHistoryAnalyzer,
)
from src.performance_engine.models import Match
from src.role_inference.services import RoleInferenceEngine

from src.carry_item_intelligence.models.carry_item_intelligence import (
    BuildProfile,
    CarryItemIntelligenceReport,
    CarryProfile,
    ItemFrequency,
    LatestCarrySnapshot,
)


class CarryItemIntelligenceEngine:
    """
    #28 — Carry + Item Intelligence

    A V2 usa o RoleInferenceEngine como única fonte de identidade do carry:
    - somente o damage_carry inferido pelo RoleInferenceEngine pode ser publicado;
    - ele só entra na análise de itens quando termina com pelo menos 2 itens;
    - não existe fallback por quantidade de itens, tier ou raridade;
    - se não houver damage_carry válido, a partida fica sem carry público.

    Isso impede que um tank, suporte ou outra unidade muito itemizada seja
    promovida artificialmente a carry.
    """

    MIN_SAMPLE = 3
    MIN_ITEMS_FOR_PUBLIC_CARRY = 2

    @classmethod
    def build(
        cls,
        *,
        matches: list[Match],
        item_classifications: dict,
    ) -> CarryItemIntelligenceReport:
        if not matches:
            raise ValueError(
                "É necessário informar ao menos uma partida."
            )

        base = ItemizationHistoryAnalyzer.analyze(
            matches,
            item_classifications=item_classifications,
        )

        observations: list[dict[str, Any]] = []

        for match in matches:
            participant = match.analyzed_participant
            if participant is None:
                continue

            role_report = RoleInferenceEngine.infer_participant(
                participant=participant,
                item_classifications=item_classifications,
            )

            carry_assessment = getattr(
                role_report,
                "damage_carry",
                None,
            )

            selected = cls._validated_carry(
                participant=participant,
                assessment=carry_assessment,
            )

            if selected is None:
                continue

            character_id, item_ids = selected

            observations.append(
                {
                    "match_id": match.match_id,
                    "placement": match.placement,
                    "character_id": character_id,
                    "item_ids": item_ids,
                }
            )

        by_carry: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for obs in observations:
            by_carry[
                obs["character_id"]
            ].append(obs)

        profiles = tuple(
            sorted(
                (
                    cls._carry_profile(
                        character_id=character_id,
                        observations=carry_observations,
                        total_matches=len(matches),
                    )
                    for character_id, carry_observations
                    in by_carry.items()
                ),
                key=lambda item: (
                    -item.matches_played,
                    item.average_placement,
                    item.character_id,
                ),
            )
        )

        most_used = (
            profiles[0]
            if profiles
            else None
        )

        supported = [
            profile
            for profile in profiles
            if profile.eligible_for_comparison
        ]

        best_supported = (
            min(
                supported,
                key=lambda item: (
                    item.average_placement,
                    -item.top4_rate,
                    -item.win_rate,
                    -item.matches_played,
                ),
            )
            if supported
            else None
        )

        latest = None

        if observations:
            latest_obs = observations[0]
            latest = LatestCarrySnapshot(
                match_id=latest_obs["match_id"],
                placement=latest_obs["placement"],
                character_id=latest_obs["character_id"],
                item_ids=latest_obs["item_ids"],
            )

        return CarryItemIntelligenceReport(
            matches_analyzed=len(matches),
            matches_with_carry=len(observations),
            carry_detection_rate=round(
                len(observations)
                / len(matches)
                * 100.0,
                2,
            ),
            itemization_score=base.score,
            itemization_label=base.label,
            carry_item_share=base.carry_item_share,
            carry_full_item_rate=base.carry_full_item_rate,
            unique_carries=len(profiles),
            carry_profiles=profiles,
            most_used_carry=most_used,
            best_supported_carry=best_supported,
            latest=latest,
            limitations=(
                "A análise usa apenas carry e itens observados no board final.",
                "Somente o carry inferido pelo RoleInferenceEngine é aceito; não há fallback por itemização.",
                "Para a análise pública de itens, o carry inferido precisa terminar com pelo menos 2 itens.",
                "A Riot API não informa em qual round cada item foi construído ou equipado.",
                "Performance histórica de um conjunto não prova que os itens causaram o resultado.",
                "Builds são comparadas apenas dentro do mesmo carry e exigem amostra mínima para leitura comparativa.",
            ),
        )

    @classmethod
    def _validated_carry(
        cls,
        *,
        participant,
        assessment,
    ) -> tuple[str, tuple[str, ...]] | None:
        """
        Valida exclusivamente o carry já inferido pelo RoleInferenceEngine V2.

        Esta camada não escolhe um substituto quando o motor de roles retorna
        None ou quando o carry inferido termina com poucos itens. Quantidade de
        itens, tier e raridade não podem promover outra unidade a carry.
        """
        if assessment is None:
            return None

        inferred_character_id = cls._assessment_character_id(
            assessment=assessment,
            participant=participant,
        )

        if not inferred_character_id:
            return None

        inferred_items = cls._assessment_item_ids(
            assessment=assessment,
            participant=participant,
            character_id=inferred_character_id,
        )

        if len(inferred_items) < cls.MIN_ITEMS_FOR_PUBLIC_CARRY:
            return None

        return (
            inferred_character_id,
            inferred_items,
        )

    @classmethod
    def _carry_profile(
        cls,
        *,
        character_id: str,
        observations: list[dict[str, Any]],
        total_matches: int,
    ) -> CarryProfile:
        placements = [
            item["placement"]
            for item in observations
        ]

        item_counter = Counter(
            item_id
            for observation in observations
            for item_id in set(
                observation["item_ids"]
            )
        )

        build_groups: dict[
            tuple[str, ...],
            list[int],
        ] = defaultdict(list)

        for observation in observations:
            build_key = tuple(
                sorted(
                    observation["item_ids"]
                )
            )

            if build_key:
                build_groups[
                    build_key
                ].append(
                    observation["placement"]
                )

        recurring_builds = tuple(
            sorted(
                (
                    BuildProfile(
                        item_ids=build,
                        matches_played=len(build_placements),
                        average_placement=round(
                            mean(build_placements),
                            2,
                        ),
                        top4_rate=round(
                            sum(
                                placement <= 4
                                for placement
                                in build_placements
                            )
                            / len(build_placements)
                            * 100.0,
                            2,
                        ),
                        win_rate=round(
                            sum(
                                placement == 1
                                for placement
                                in build_placements
                            )
                            / len(build_placements)
                            * 100.0,
                            2,
                        ),
                        eligible_for_comparison=(
                            len(build_placements)
                            >= cls.MIN_SAMPLE
                        ),
                    )
                    for build, build_placements
                    in build_groups.items()
                ),
                key=lambda item: (
                    -item.matches_played,
                    item.average_placement,
                    item.item_ids,
                ),
            )[:5]
        )

        return CarryProfile(
            character_id=character_id,
            matches_played=len(observations),
            usage_rate=round(
                len(observations)
                / total_matches
                * 100.0,
                2,
            ),
            average_placement=round(
                mean(placements),
                2,
            ),
            top4_rate=round(
                sum(
                    placement <= 4
                    for placement in placements
                )
                / len(placements)
                * 100.0,
                2,
            ),
            win_rate=round(
                sum(
                    placement == 1
                    for placement in placements
                )
                / len(placements)
                * 100.0,
                2,
            ),
            full_build_rate=round(
                sum(
                    len(item["item_ids"]) >= 3
                    for item in observations
                )
                / len(observations)
                * 100.0,
                2,
            ),
            eligible_for_comparison=(
                len(observations)
                >= cls.MIN_SAMPLE
            ),
            most_used_items=tuple(
                ItemFrequency(
                    item_id=item_id,
                    matches_observed=count,
                    match_rate=round(
                        count
                        / len(observations)
                        * 100.0,
                        2,
                    ),
                )
                for item_id, count
                in item_counter.most_common(6)
            ),
            recurring_builds=recurring_builds,
        )

    @staticmethod
    def _assessment_character_id(
        *,
        assessment,
        participant,
    ) -> str:
        for field_name in (
            "character_id",
            "unit_character_id",
            "unit_id",
        ):
            value = str(
                getattr(
                    assessment,
                    field_name,
                    "",
                )
                or ""
            ).strip()

            if value:
                return value

        assessment_items = tuple(
            getattr(
                assessment,
                "item_ids",
                (),
            )
            or ()
        )

        if assessment_items:
            for unit in participant.units:
                unit_items = CarryItemIntelligenceEngine._unit_item_ids(
                    unit
                )

                if (
                    unit_items
                    and tuple(unit_items)
                    == tuple(assessment_items)
                ):
                    return str(
                        getattr(
                            unit,
                            "character_id",
                            "",
                        )
                        or ""
                    )

        return ""

    @staticmethod
    def _assessment_item_ids(
        *,
        assessment,
        participant,
        character_id: str,
    ) -> tuple[str, ...]:
        direct = tuple(
            str(item)
            for item in (
                getattr(
                    assessment,
                    "item_ids",
                    (),
                )
                or ()
            )
            if str(item).strip()
        )

        if direct:
            return direct

        for unit in participant.units:
            if (
                str(
                    getattr(
                        unit,
                        "character_id",
                        "",
                    )
                    or ""
                )
                == character_id
            ):
                return CarryItemIntelligenceEngine._unit_item_ids(
                    unit
                )

        return ()

    @staticmethod
    def _unit_item_ids(
        unit,
    ) -> tuple[str, ...]:
        for field_name in (
            "item_ids",
            "item_names",
            "items",
        ):
            value = getattr(
                unit,
                field_name,
                None,
            )

            if value:
                return tuple(
                    str(item)
                    for item in value
                    if str(item).strip()
                )

        return ()

    @staticmethod
    def _safe_int(
        value,
    ) -> int:
        try:
            return int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0
