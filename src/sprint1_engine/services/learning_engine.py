from __future__ import annotations

from src.performance_engine.models import Match
from src.sprint1_engine.models import LearningCycleResult
from src.sprint1_engine.repositories import KnowledgeRepository


class KnowledgeLearningEngine:
    TRANSFORMER_VERSION = "match_transformer_v1"
    LEARNING_VERSION = "sprint1_learning_v1"

    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def learn(
        self,
        *,
        matches: list[Match],
        source: str,
        patch: str = "",
        set_number: int | None = None,
        game_datetimes: dict[str, int] | None = None,
        contest_scores: dict[str, float] | None = None,
        composition_keys: dict[str, str] | None = None,
    ) -> LearningCycleResult:
        if source not in {"player", "challenger"}:
            raise ValueError("source deve ser player ou challenger.")

        self.repository.initialize()
        inserted = reused = observations = 0
        game_datetimes = game_datetimes or {}
        contest_scores = contest_scores or {}
        composition_keys = composition_keys or {}

        for match in matches:
            participant = match.analyzed_participant
            puuid = (
                participant.puuid
                if participant is not None
                else match.analyzed_player_puuid
            )
            if not puuid:
                continue

            if self.repository.is_processed(
                match_id=match.match_id,
                source=source,
                player_puuid=puuid,
                transformer_version=self.TRANSFORMER_VERSION,
                learning_version=self.LEARNING_VERSION,
            ):
                reused += 1
                continue

            self.repository.save_match(
                values={
                    "match_id": match.match_id,
                    "source": source,
                    "player_puuid": puuid,
                    "patch": patch,
                    "set_number": set_number,
                    "game_datetime": game_datetimes.get(match.match_id),
                    "transformer_version": self.TRANSFORMER_VERSION,
                    "learning_version": self.LEARNING_VERSION,
                    "placement": match.placement,
                    "level": match.level,
                    "gold_left": match.gold_left,
                    "last_round": match.last_round,
                    "players_eliminated": match.players_eliminated,
                    "total_damage_to_players": match.total_damage_to_players,
                }
            )

            if participant is not None:
                for unit in participant.units:
                    self._observe(
                        "unit", unit.character_id, source, patch, set_number,
                        match, contest_scores.get(match.match_id, 0.0),
                        {"tier": unit.tier, "rarity": unit.rarity},
                    )
                    observations += 1
                    for item_id in unit.items:
                        self._observe(
                            "item", item_id, source, patch, set_number,
                            match, contest_scores.get(match.match_id, 0.0),
                            {"unit": unit.character_id},
                        )
                        observations += 1
                for trait in participant.active_traits:
                    self._observe(
                        "trait", trait.name, source, patch, set_number,
                        match, contest_scores.get(match.match_id, 0.0),
                        {"num_units": trait.num_units},
                    )
                    observations += 1

            composition_key = composition_keys.get(match.match_id)
            if composition_key:
                self._observe(
                    "composition", composition_key, source, patch, set_number,
                    match, contest_scores.get(match.match_id, 0.0), {},
                )
                observations += 1

            economy_bucket = (
                "level_9" if match.level >= 9
                else "level_8" if match.level >= 8
                else "level_7_or_lower"
            )
            self._observe(
                "economy", economy_bucket, source, patch, set_number,
                match, contest_scores.get(match.match_id, 0.0), {},
            )
            observations += 1
            inserted += 1

        return LearningCycleResult(
            matches_received=len(matches),
            matches_inserted=inserted,
            matches_reused=reused,
            observations_written=observations,
            database_path=str(self.repository.path),
        )

    def _observe(
        self,
        dimension: str,
        key: str,
        source: str,
        patch: str,
        set_number: int | None,
        match: Match,
        contest_score: float,
        payload: dict,
    ) -> None:
        self.repository.upsert_observation(
            dimension=dimension,
            observation_key=key,
            source=source,
            patch=patch,
            set_number=set_number,
            placement=match.placement,
            level=match.level,
            gold_left=match.gold_left,
            contest_score=contest_score,
            payload=payload,
        )
