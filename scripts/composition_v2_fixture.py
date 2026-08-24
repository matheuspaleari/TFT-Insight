from __future__ import annotations

from src.performance_engine.models import (
    Match,
    ParticipantSnapshot,
    TraitSnapshot,
    UnitSnapshot,
)


def unit(cid, *, rarity=2, tier=2, items=()):
    return UnitSnapshot(
        character_id=cid,
        rarity=rarity,
        tier=tier,
        items=tuple(items),
    )


def trait(name, units, tier=1, style=1):
    return TraitSnapshot(
        name=name,
        num_units=units,
        tier_current=tier,
        tier_total=max(tier, 1),
        style=style,
    )


def match(
    match_id,
    placement,
    *,
    units,
    traits,
    level=8,
    gold=10,
):
    puuid = "PLAYER"
    participant = ParticipantSnapshot(
        puuid=puuid,
        placement=placement,
        level=level,
        gold_left=gold,
        last_round=30,
        players_eliminated=1,
        total_damage_to_players=80,
        time_eliminated=1800.0,
        units=tuple(units),
        traits=tuple(traits),
    )
    return Match(
        match_id=match_id,
        placement=placement,
        level=level,
        gold_left=gold,
        last_round=30,
        players_eliminated=1,
        total_damage_to_players=80,
        time_eliminated=1800.0,
        analyzed_player_puuid=puuid,
        participants=(participant,),
    )


def composition_a(mid, placement):
    return match(
        mid,
        placement,
        units=(
            unit("CarryA", rarity=4, tier=2, items=("I1","I2","I3")),
            unit("TankA", rarity=4, tier=2, items=("T1","T2")),
            unit("CoreA1"),
            unit("CoreA2"),
            unit("FlexA"),
        ),
        traits=(
            trait("TraitA", 4, tier=2, style=2),
            trait("TraitB", 2, tier=1, style=1),
            trait("TFT17_HPTank", 2, tier=1, style=1),
        ),
    )


def composition_a_variant(mid, placement):
    return match(
        mid,
        placement,
        units=(
            unit("CarryA", rarity=4, tier=2, items=("I1","I2","I3")),
            unit("TankA", rarity=4, tier=2, items=("T1","T2")),
            unit("CoreA1"),
            unit("CoreA2"),
            unit("FlexB"),
        ),
        traits=(
            trait("TraitA", 4, tier=2, style=2),
            trait("TraitB", 2, tier=1, style=1),
        ),
    )


def composition_b(mid, placement):
    return match(
        mid,
        placement,
        units=(
            unit("CarryB", rarity=4, tier=2, items=("X1","X2","X3")),
            unit("TankB", rarity=4, tier=2, items=("Y1","Y2")),
            unit("CoreB1"),
            unit("CoreB2"),
            unit("FlexC"),
        ),
        traits=(
            trait("TraitC", 4, tier=2, style=2),
            trait("TraitD", 2, tier=1, style=1),
        ),
    )
