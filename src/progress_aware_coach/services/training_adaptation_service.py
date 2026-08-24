from __future__ import annotations

class TrainingAdaptationService:
    """Fase 13.5: converte a estratégia longitudinal em orientação de treino, sem mutar missão."""

    @classmethod
    def build(cls, *, progress_strategy: dict, adaptive_strategy: dict) -> dict:
        action = str(progress_strategy.get("action", "MAINTAIN")).upper()
        task_id = adaptive_strategy.get("current_task_id")
        difficulty = adaptive_strategy.get("current_difficulty")

        if action == "REINFORCE_FOUNDATION":
            mode = "REINFORCE"
            instruction = "Reforce a execução do exercício atual e evite aumentar a dificuldade até a sequência de queda ser interrompida."
        elif action == "RECOGNIZE_AND_PREPARE_ADVANCE":
            mode = "PREPARE_PROGRESSION"
            instruction = "Reconheça a melhora consistente e prepare o próximo degrau, mas deixe a progressão formal para o Learning Loop."
        elif action == "OBSERVE":
            mode = "KEEP_AND_OBSERVE"
            instruction = "Mantenha o exercício e a dificuldade atuais. Colete mais evidência antes de simplificar ou avançar."
        else:
            mode = "KEEP_CURRENT"
            instruction = "Mantenha a abordagem atual; o histórico ainda não justifica uma adaptação específica."

        return {
            "mode": mode,
            "task_id": task_id,
            "difficulty": difficulty,
            "instruction": instruction,
            "changes_mission": False,
            "changes_priority": False,
            "changes_difficulty": False,
        }
