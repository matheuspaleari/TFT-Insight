"""
Serviço responsável pela missão ativa e seu progresso.
"""

from dataclasses import replace

from src.learning.models import LearningRecommendation
from src.storage import PlayerRepository
from src.training.knowledge import get_tasks_for_skill
from src.training.models import TrainingMission
from src.training.models.training_plan import TrainingPlan

from .mission_generator import MissionGenerator
from .learning_loop_orchestrator import LearningLoopOrchestrator
from .pedagogical_memory_service import PedagogicalMemoryService


class PlayerTrainingService:
    """
    Política V2:

    1. Uma missão ativa nunca é interrompida por uma prioridade nova.
    2. Partidas novas são contadas pelo baseline de match_ids.
    3. Match IDs duplicados nunca avançam o progresso duas vezes.
    4. Depois de 5/5, a próxima análise pode criar a nova missão.
    """

    def __init__(
        self,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.player_repository = (
            player_repository
            or PlayerRepository()
        )

        # Estado transitório da análise atual.
        self._completed_this_run: set[str] = set()

    def sync_mission_progress(
        self,
        *,
        puuid: str,
        current_match_ids: tuple[str, ...],
    ) -> TrainingMission | None:
        """
        Atualiza o progresso da missão usando a janela atual de partidas.

        Missões antigas sem baseline são migradas com segurança: o estado
        atual vira baseline e apenas partidas futuras serão contabilizadas.
        Não há inferência retroativa automática.
        """

        mission = (
            self.player_repository.load_training_mission(
                puuid=puuid,
            )
        )

        if mission is None:
            return None

        if mission.is_completed:
            return mission

        current_match_ids = tuple(
            str(item)
            for item in current_match_ids
        )

        if not mission.baseline_match_ids:
            migrated = replace(
                mission,
                baseline_match_ids=current_match_ids,
            )

            self.player_repository.save_training_mission(
                puuid=puuid,
                mission=migrated,
            )

            print(
                "Missão antiga sem baseline encontrada. "
                "Baseline inicializado com segurança; "
                "o progresso automático começa nas próximas partidas."
            )

            return migrated

        baseline = set(
            mission.baseline_match_ids
        )
        completed = set(
            mission.completed_match_ids
        )

        # Riot normalmente retorna do mais recente para o mais antigo.
        # Invertemos para registrar o progresso em ordem cronológica.
        new_match_ids = tuple(
            match_id
            for match_id in reversed(
                current_match_ids
            )
            if match_id not in baseline
            and match_id not in completed
        )

        if not new_match_ids:
            return mission

        accepted = new_match_ids[
            :mission.remaining_games
        ]

        if not accepted:
            return mission

        completed_match_ids = (
            mission.completed_match_ids
            + accepted
        )

        updated = replace(
            mission,
            games_completed=len(
                completed_match_ids
            ),
            completed_match_ids=(
                completed_match_ids
            ),
        )

        self.player_repository.save_training_mission(
            puuid=puuid,
            mission=updated,
        )

        if updated.is_completed:
            cycle_path = (
                self.player_repository.archive_training_cycle(
                    puuid=puuid,
                    mission=updated,
                )
            )
            self._completed_this_run.add(
                updated.mission_id
            )
            print(
                "Ciclo de treinamento arquivado em: "
                f"{cycle_path}"
            )

        print(
            "Progresso da missão atualizado: "
            f"{updated.games_completed}/"
            f"{updated.games_target}"
        )

        return updated

    def get_or_create_mission(
        self,
        *,
        puuid: str,
        recommendation: LearningRecommendation,
        games_target: int = 5,
        baseline_match_ids: tuple[str, ...] = (),
    ) -> TrainingMission:
        stored_mission = (
            self.player_repository.load_training_mission(
                puuid=puuid,
            )
        )

        if (
            stored_mission is not None
            and not stored_mission.is_completed
        ):
            print(
                "Missão ativa encontrada. "
                "Mantendo o ciclo atual antes de iniciar outro."
            )
            return stored_mission

        if (
            stored_mission is not None
            and stored_mission.is_completed
        ):
            self.player_repository.archive_training_cycle(
                puuid=puuid,
                mission=stored_mission,
            )

            if (
                stored_mission.mission_id
                in self._completed_this_run
            ):
                self._completed_this_run.discard(
                    stored_mission.mission_id
                )
                print(
                    "Missão concluída nesta análise. "
                    "Mantendo 5/5 visível antes do próximo ciclo."
                )
                return stored_mission

        mission = MissionGenerator.generate(
            recommendation=recommendation,
            games_target=games_target,
            baseline_match_ids=baseline_match_ids,
        )

        return self._save(
            puuid=puuid,
            mission=mission,
        )

    def get_or_create_mission_from_plan(
        self,
        *,
        puuid: str,
        training_plan: TrainingPlan,
        baseline_match_ids: tuple[str, ...] = (),
    ) -> TrainingMission:
        stored_mission = (
            self.player_repository.load_training_mission(
                puuid=puuid,
            )
        )

        # Regra de produto: prioridade nova espera a missão atual terminar.
        if (
            stored_mission is not None
            and not stored_mission.is_completed
        ):
            print(
                "Missão ativa encontrada. "
                "Mantendo o ciclo atual antes de iniciar outro."
            )
            return stored_mission

        if (
            stored_mission is not None
            and stored_mission.is_completed
        ):
            self.player_repository.archive_training_cycle(
                puuid=puuid,
                mission=stored_mission,
            )

            if (
                stored_mission.mission_id
                in self._completed_this_run
            ):
                self._completed_this_run.discard(
                    stored_mission.mission_id
                )
                print(
                    "Missão concluída nesta análise. "
                    "Mantendo 5/5 visível antes do próximo ciclo."
                )
                return stored_mission

        decision = None

        if (
            stored_mission is not None
            and stored_mission.is_completed
        ):
            training_history = (
                self.player_repository.list_training_cycles(
                    puuid=puuid
                )
            )

            decision = LearningLoopOrchestrator.decide(
                priority_skill_id=(
                    training_plan.primary_skill_id
                ),
                completed_mission=(
                    stored_mission.to_dict()
                ),
                training_history=training_history,
            )

            self._record_learning_loop_decision(
                puuid=puuid,
                decision=decision.to_dict(),
            )

            if decision.defer_new_mission:
                print(
                    "Learning Loop: nova missão adiada por "
                    "COOLDOWN_SKILL; aguardando reavaliação "
                    "da prioridade."
                )
                return stored_mission

        if (
            decision is not None
            and decision.selected_task_id
        ):
            task = self._select_task_by_id(
                skill_id=(
                    training_plan.primary_skill_id
                ),
                task_id=(
                    decision.selected_task_id
                ),
            )

            mission = TrainingMission(
                task=task,
                games_target=(
                    training_plan.games_target
                ),
                baseline_match_ids=(
                    baseline_match_ids
                ),
            )

            print(
                "Learning Loop aplicado: "
                f"{decision.post_cycle_action} -> "
                f"{decision.anti_loop_action} -> "
                f"{decision.progression_signal} -> "
                f"{task.id} ({task.difficulty})"
            )

        else:
            mission = (
                MissionGenerator.generate_from_plan(
                    training_plan=training_plan,
                    baseline_match_ids=baseline_match_ids,
                )
            )

        return self._save(
            puuid=puuid,
            mission=mission,
        )

    @staticmethod
    def _select_task_by_id(
        *,
        skill_id: str,
        task_id: str,
    ):
        tasks = get_tasks_for_skill(
            skill_id
        )

        for task in tasks:
            if task.id == task_id:
                return task

        raise RuntimeError(
            "O Post-Cycle Decision sugeriu uma task "
            "que não existe no catálogo da Skill: "
            f"{skill_id}/{task_id}"
        )

    def _record_learning_loop_decision(
        self,
        *,
        puuid: str,
        decision: dict,
    ) -> None:
        if not (
            hasattr(
                self.player_repository,
                "load_pedagogical_memory",
            )
            and hasattr(
                self.player_repository,
                "save_pedagogical_memory",
            )
        ):
            return

        PedagogicalMemoryService(
            player_repository=(
                self.player_repository
            )
        ).record_decision(
            puuid=puuid,
            decision=decision,
        )

    def _save(
        self,
        *,
        puuid: str,
        mission: TrainingMission,
    ) -> TrainingMission:
        mission_path = (
            self.player_repository.save_training_mission(
                puuid=puuid,
                mission=mission,
            )
        )

        print(
            "Nova missão persistida em: "
            f"{mission_path}"
        )

        return mission
