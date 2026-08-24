from pathlib import Path
import tempfile
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.performance_engine.models import (
    Match,
    ParticipantSnapshot,
    TraitSnapshot,
    UnitSnapshot,
)
from src.sprint1_engine import (
    CrossAnalyzer,
    KnowledgeLearningEngine,
    KnowledgeRepository,
    PregameGuidanceEngine,
    Sprint1Formatter,
    SprintPredictionEngine,
)


def build_match(index: int, source: str) -> Match:
    placement = (index % 8) + 1
    participant = ParticipantSnapshot(
        puuid=f"{source}-player-{index}",
        placement=placement,
        level=9 if placement <= 2 else 8,
        gold_left=index % 15,
        last_round=38 - placement,
        players_eliminated=max(0, 4 - placement // 2),
        total_damage_to_players=150 - placement * 10,
        time_eliminated=2000.0,
        traits=(TraitSnapshot(name="TFT_TestTrait", num_units=4, style=1, tier_current=1),),
        units=(
            UnitSnapshot(
                character_id="TFT_TestCarry",
                rarity=4,
                tier=2,
                items=("TFT_Item_IE", "TFT_Item_Guinsoo", "TFT_Item_LW"),
            ),
            UnitSnapshot(
                character_id="TFT_TestTank",
                rarity=4,
                tier=2,
                items=("TFT_Item_Warmog", "TFT_Item_Gargoyle"),
            ),
        ),
    )
    return Match(
        match_id=f"{source}-match-{index}",
        placement=participant.placement,
        level=participant.level,
        gold_left=participant.gold_left,
        last_round=participant.last_round,
        players_eliminated=participant.players_eliminated,
        total_damage_to_players=participant.total_damage_to_players,
        time_eliminated=participant.time_eliminated,
        analyzed_player_puuid=participant.puuid,
        participants=(participant,),
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repository = KnowledgeRepository(Path(temporary) / "knowledge.db")
        learning = KnowledgeLearningEngine(repository)

        challenger = [build_match(i, "challenger") for i in range(80)]
        player = [build_match(i, "player") for i in range(20)]

        challenger_result = learning.learn(
            matches=challenger,
            source="challenger",
            patch="16.15",
            set_number=17,
        )
        player_result = learning.learn(
            matches=player,
            source="player",
            patch="16.15",
            set_number=17,
        )
        reused_result = learning.learn(
            matches=player,
            source="player",
            patch="16.15",
            set_number=17,
        )

        prediction = SprintPredictionEngine.predict(
            history_matches=player,
            strategic_score=76.0,
            contest_score=53.0,
            flex_score=71.0,
            knowledge_repository=repository,
            patch="16.15",
            set_number=17,
        )
        guidance = PregameGuidanceEngine.build(
            carry_contest_rate=50.0,
            high_contest_rate=25.0,
            level_8_rate=85.0,
            level_9_rate=40.0,
            carry_full_item_rate=60.0,
            tank_full_item_rate=75.0,
            sample_size=20,
        )
        cross = CrossAnalyzer.analyze(
            strategic_score=76.0,
            economy_score=82.0,
            itemization_score=76.0,
            tempo_score=71.0,
            contest_score=53.0,
            flex_score=71.0,
            sample_size=20,
        )

        assert challenger_result.matches_inserted == 80
        assert player_result.matches_inserted == 20
        assert reused_result.matches_reused == 20
        assert 0 <= prediction.top4_probability <= 100
        assert guidance.pivot_attention
        assert cross.label
        Sprint1Formatter.to_dict(prediction)

        print("=" * 88)
        print("TFT INSIGHT - SPRINT 1 INTEGRATED VALIDATION")
        print("=" * 88)
        print(f"Challenger inseridas : {challenger_result.matches_inserted}")
        print(f"Player inseridas     : {player_result.matches_inserted}")
        print(f"Player reutilizadas  : {reused_result.matches_reused}")
        print(f"Top 1                : {prediction.top1_probability:.2f}%")
        print(f"Top 4                : {prediction.top4_probability:.2f}%")
        print(f"Bot 4                : {prediction.bot4_probability:.2f}%")
        print(f"Colocação esperada   : {prediction.expected_placement:.2f}")
        print(f"Confiança            : {prediction.confidence.score:.2f}%")
        print(f"Cross score          : {cross.score:.2f} ({cross.label})")
        print(guidance.pivot_attention)
        print(guidance.win_condition)
        print("✓ Prediction → Learning → Confidence → Cross → SQLite validados.")


if __name__ == "__main__":
    main()
