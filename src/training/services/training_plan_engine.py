from __future__ import annotations
from src.learning.models.learning_priority import LearningPriorityPlan
from src.training.models.training_plan import TrainingExercise, TrainingPlan

class TrainingPlanEngine:
    DEFAULT_GAMES_TARGET = 5

    @classmethod
    def build(cls, *, priority_plan: LearningPriorityPlan, games_target: int = DEFAULT_GAMES_TARGET) -> TrainingPlan | None:
        primary = priority_plan.primary
        if primary is None:
            return None
        if games_target <= 0:
            raise ValueError("games_target deve ser maior que zero.")

        exercise = cls._exercise_for(primary.skill_id, primary.training_focus)

        return TrainingPlan(
            primary_skill_id=primary.skill_id,
            primary_skill_label=primary.skill_label,
            objective=primary.training_focus,
            games_target=games_target,
            exercise=exercise,
            secondary_focus=tuple(
                f"{item.skill_label}: {item.training_focus}"
                for item in priority_plan.secondary
            ),
            strengths_to_preserve=tuple(
                f"{item.skill_label}: preservar enquanto o foco principal é treinado."
                for item in priority_plan.strengths
            ),
            contexts_to_watch=tuple(
                f"{item.skill_label}: observar, sem transformar em deficiência ou prioridade oficial."
                for item in priority_plan.context
            ),
            rationale=primary.reason,
            confidence=primary.confidence,
            limitations=primary.limitations,
        )

    @classmethod
    def _exercise_for(cls, skill_id: str, training_focus: str) -> TrainingExercise:
        return {
            "consistency": cls._consistency,
            "leveling": cls._leveling,
            "board_pressure": cls._board_pressure,
            "economy": cls._economy,
        }.get(skill_id, cls._generic)(training_focus)

    @staticmethod
    def _consistency(training_focus: str) -> TrainingExercise:
        return TrainingExercise(
            exercise_id="consistency_decision_checkpoint",
            title="Checkpoint de decisão",
            instruction=(
                "Durante as próximas partidas, escolha uma decisão principal por etapa importante "
                "e evite trocar de plano sem um motivo observável. Antes de mudar a linha, "
                "identifique qual informação do lobby ou do seu tabuleiro justificou a mudança."
            ),
            checklist=(
                "Antes de uma mudança importante, identificar o motivo concreto.",
                "Evitar mudar duas decisões grandes ao mesmo tempo.",
                "Ao final da partida, lembrar qual decisão mais alterou o plano.",
            ),
            success_signals=(
                "Menos mudanças de plano sem justificativa clara.",
                "Decisões mais fáceis de explicar após a partida.",
                "Resultados menos dependentes de correções tardias improvisadas.",
            ),
            system_verification=(
                "Parcial. O TFT Insight acompanha resultados e consistência agregada, "
                "mas ainda não observa todas as decisões dentro da partida."
            ),
        )

    @staticmethod
    def _leveling(training_focus: str) -> TrainingExercise:
        return TrainingExercise(
            exercise_id="leveling_timing_review",
            title="Ritmo de progressão",
            instruction=(
                "Trate o Leveling como decisão de timing. Antes de comprar experiência, "
                "confirme se a progressão serve ao estado atual da partida, em vez de subir "
                "de nível apenas por hábito."
            ),
            checklist=(
                "Identificar o objetivo antes de comprar experiência.",
                "Comparar estabilização com preservação de recursos.",
                "Após a partida, revisar se a progressão veio cedo, tarde ou no momento esperado.",
            ),
            success_signals=(
                "Progressão mais alinhada ao estado da partida.",
                "Menos subidas automáticas sem objetivo claro.",
                "Manutenção da capacidade de chegar a níveis altos.",
            ),
            system_verification=(
                "Parcial. O sistema observa nível agregado, mas não reconstrói o timing exato de XP."
            ),
        )

    @staticmethod
    def _board_pressure(training_focus: str) -> TrainingExercise:
        return TrainingExercise(
            exercise_id="board_pressure_conversion",
            title="Converter força em pressão",
            instruction="Preserve a capacidade de converter um tabuleiro forte em dano e eliminações sem gastar recursos desnecessariamente.",
            checklist=("Reconhecer quando o tabuleiro já está estável.", "Evitar gastar por força marginal."),
            success_signals=("Pressão mantida com eficiência.",),
            system_verification="Parcial. Dano e eliminações são observáveis, mas não explicam todas as decisões.",
        )

    @staticmethod
    def _economy(training_focus: str) -> TrainingExercise:
        return TrainingExercise(
            exercise_id="economy_observation",
            title="Observar decisões de recursos",
            instruction="Observe quando decide guardar ou gastar recursos; não transformar isso em prescrição forte enquanto faltarem métricas diretas.",
            checklist=("Identificar o motivo antes de um gasto relevante.",),
            success_signals=("Decisões econômicas mais fáceis de explicar.",),
            system_verification="Limitada. Ainda faltam métricas diretas suficientes.",
        )

    @staticmethod
    def _generic(training_focus: str) -> TrainingExercise:
        return TrainingExercise(
            exercise_id="focused_skill_cycle",
            title="Ciclo de foco",
            instruction=training_focus,
            checklist=("Manter uma única Skill como foco principal.", "Revisar após a partida se o foco foi aplicado."),
            success_signals=("Execução mais consciente do foco escolhido.",),
            system_verification="Depende das métricas disponíveis para a Skill.",
        )
