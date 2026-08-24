from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

class MissionCycleStage(StrEnum):
    START = "start"
    EARLY = "early"
    MID = "mid"
    FINAL = "final"
    COMPLETED = "completed"

@dataclass(frozen=True, slots=True)
class MissionCycleState:
    stage: MissionCycleStage
    label: str
    message: str

class MissionCycleStageResolver:
    @classmethod
    def resolve(cls, *, games_completed: int, games_target: int) -> MissionCycleState:
        if games_target < 1:
            raise ValueError("games_target deve ser maior que zero.")
        completed = max(0, min(int(games_completed), int(games_target)))
        if completed >= games_target:
            return MissionCycleState(MissionCycleStage.COMPLETED, "Ciclo concluído", "Você concluiu as partidas previstas para este ciclo. O TFT Insight já pode reavaliar o foco com os dados atuais.")
        if completed == 0:
            return MissionCycleState(MissionCycleStage.START, "Início do ciclo", "Este ciclo acabou de começar. Mantenha o exercício atual por algumas partidas antes de tirar conclusões.")
        remaining = games_target - completed
        if remaining == 1:
            return MissionCycleState(MissionCycleStage.FINAL, "Consolidação", "Falta uma partida para concluir este ciclo. Mantenha o exercício atual e evite mudar o foco agora.")
        if completed / games_target >= 0.5:
            return MissionCycleState(MissionCycleStage.MID, "Meio do ciclo", "Você chegou à parte central do ciclo. Continue repetindo o mesmo exercício e não reaja demais a uma partida isolada.")
        return MissionCycleState(MissionCycleStage.EARLY, "Construindo evidência", "O ciclo ainda está no começo. Continue com o mesmo exercício para acumular evidência antes de avaliar o resultado.")
