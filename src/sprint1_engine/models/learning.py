from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LearningCycleResult:
    matches_received: int
    matches_inserted: int
    matches_reused: int
    observations_written: int
    database_path: str
