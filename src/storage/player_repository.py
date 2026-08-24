"""
Repositório responsável por persistir o estado de cada jogador.

Cada jogador possui uma pasta própria, identificada por um hash
estável gerado a partir de seu PUUID.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.performance_engine.models import Performance
from src.training.models import TrainingMission


class PlayerRepository:
    """
    Gerencia os dados persistentes de um jogador.

    Responsabilidades:

    - criar automaticamente a estrutura de diretórios;
    - persistir e atualizar o perfil;
    - salvar e recuperar análises de Performance;
    - preparar pastas para Learning, Coach, Progress e History.
    """

    DEFAULT_DIRECTORY = Path("data/players")

    SUBDIRECTORIES = (
        "performance",
        "learning",
        "training",
        "coach",
        "progress",
        "history",
    )

    def __init__(
        self,
        players_directory: str | Path = DEFAULT_DIRECTORY,
    ) -> None:
        self.players_directory = Path(players_directory)

    def ensure_player(
        self,
        *,
        puuid: str,
        game_name: str,
        tag_line: str,
    ) -> Path:
        """
        Cria, quando necessário, toda a estrutura do jogador.

        Também cria ou atualiza o profile.json.
        """

        self._validate_puuid(puuid)

        player_directory = self.get_player_directory(
            puuid=puuid,
        )

        player_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for subdirectory in self.SUBDIRECTORIES:
            (
                player_directory
                / subdirectory
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

        self._save_profile(
            puuid=puuid,
            game_name=game_name,
            tag_line=tag_line,
        )

        return player_directory

    def get_player_directory(
        self,
        *,
        puuid: str,
    ) -> Path:
        """
        Retorna o caminho persistente do jogador.
        """

        self._validate_puuid(puuid)

        player_id = hashlib.sha256(
            puuid.encode("utf-8")
        ).hexdigest()

        return self.players_directory / player_id

    def load_profile(
        self,
        *,
        puuid: str,
    ) -> dict[str, Any] | None:
        """
        Carrega o profile.json do jogador.
        """

        profile_path = (
            self.get_player_directory(puuid=puuid)
            / "profile.json"
        )

        data = self._read_json(profile_path)

        if not isinstance(data, dict):
            return None

        return data

    def load_performance(
        self,
        *,
        puuid: str,
        benchmark_id: str,
        match_ids: list[str],
        benchmark_fingerprint: str,
    ) -> Performance | None:
        """
        Carrega a Performance quando a análise persistida continua válida.

        A análise é válida quando:

        - o benchmark é o mesmo;
        - o conteúdo do benchmark não mudou;
        - os IDs das partidas continuam iguais.
        """

        performance_path = self._get_performance_path(
            puuid=puuid,
            benchmark_id=benchmark_id,
        )

        data = self._read_json(performance_path)

        if not isinstance(data, dict):
            return None

        metadata = data.get("metadata")
        performance_data = data.get("performance")

        if not isinstance(metadata, dict):
            return None

        if not isinstance(performance_data, dict):
            return None

        if metadata.get("match_ids") != match_ids:
            return None

        if metadata.get("benchmark_id") != benchmark_id:
            return None

        if (
            metadata.get("benchmark_fingerprint")
            != benchmark_fingerprint
        ):
            return None

        try:
            return Performance.from_dict(
                performance_data
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

    def save_performance(
        self,
        *,
        puuid: str,
        benchmark_id: str,
        benchmark_fingerprint: str,
        match_ids: list[str],
        performance: Performance,
    ) -> Path:
        """
        Salva a análise de Performance do jogador.
        """

        performance_path = self._get_performance_path(
            puuid=puuid,
            benchmark_id=benchmark_id,
        )

        data: dict[str, Any] = {
            "metadata": {
                "benchmark_id": benchmark_id,
                "benchmark_fingerprint": (
                    benchmark_fingerprint
                ),
                "match_ids": list(match_ids),
                "created_at": self._utc_now(),
            },
            "performance": performance.to_dict(),
        }

        self._write_json(
            path=performance_path,
            data=data,
        )

        self._update_last_analysis(
            puuid=puuid,
            benchmark_id=benchmark_id,
        )

        return performance_path

    def clear_performance(
        self,
        *,
        puuid: str,
        benchmark_id: str,
    ) -> bool:
        """
        Remove uma análise de Performance específica.
        """

        performance_path = self._get_performance_path(
            puuid=puuid,
            benchmark_id=benchmark_id,
        )

        if not performance_path.exists():
            return False

        performance_path.unlink()

        return True

    def save_learning_recommendation(
        self,
        *,
        puuid: str,
        benchmark_id: str,
        match_ids: list[str],
        recommendation_data: dict[str, Any],
    ) -> Path:
        """
        Salva a recomendação atual do Learning Engine.
        """

        learning_path = (
            self.get_player_directory(
                puuid=puuid,
            )
            / "learning"
            / "current.json"
        )

        data: dict[str, Any] = {
            "metadata": {
                "benchmark_id": benchmark_id,
                "match_ids": list(match_ids),
                "created_at": self._utc_now(),
            },
            "recommendation": recommendation_data,
        }

        self._write_json(
            path=learning_path,
            data=data,
        )

        return learning_path

    def load_learning_recommendation(
        self,
        *,
        puuid: str,
    ) -> dict[str, Any] | None:
        """
        Carrega a recomendação atual do Learning Engine.
        """

        learning_path = (
            self.get_player_directory(
                puuid=puuid,
            )
            / "learning"
            / "current.json"
        )

        data = self._read_json(
            path=learning_path,
        )

        if not isinstance(
            data,
            dict,
        ):
            return None

        return data

    def save_training_mission(
        self,
        *,
        puuid: str,
        mission: TrainingMission,
    ) -> Path:
        """
        Salva a missão ativa do jogador.
        """

        mission_path = (
            self.get_player_directory(
                puuid=puuid,
            )
            / "training"
            / "current.json"
        )

        data: dict[str, Any] = {
            "metadata": {
                "updated_at": self._utc_now(),
            },
            "mission": mission.to_dict(),
        }

        self._write_json(
            path=mission_path,
            data=data,
        )

        return mission_path

    def save_pedagogical_memory(
        self,
        *,
        puuid: str,
        memory: dict[str, Any],
    ) -> Path:
        """
        Persiste a memória pedagógica derivada do histórico de treino.
        """

        path = (
            self.get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "pedagogical_memory.json"
        )

        self._write_json(
            path=path,
            data=memory,
        )

        return path

    def load_pedagogical_memory(
        self,
        *,
        puuid: str,
    ) -> dict[str, Any] | None:
        path = (
            self.get_player_directory(
                puuid=puuid
            )
            / "learning"
            / "pedagogical_memory.json"
        )

        data = self._read_json(
            path=path
        )

        return (
            data
            if isinstance(data, dict)
            else None
        )

    def load_training_mission(
        self,
        *,
        puuid: str,
    ) -> TrainingMission | None:
        """
        Carrega a missão ativa do jogador.
        """

        mission_path = (
            self.get_player_directory(
                puuid=puuid,
            )
            / "training"
            / "current.json"
        )

        data = self._read_json(
            path=mission_path,
        )

        if not isinstance(data, dict):
            return None

        mission_data = data.get("mission")

        if not isinstance(mission_data, dict):
            return None

        try:
            return TrainingMission.from_dict(
                mission_data
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            return None


    def archive_training_cycle(
        self,
        *,
        puuid: str,
        mission: TrainingMission,
    ) -> Path:
        """Arquiva uma missão concluída de forma idempotente."""

        if not mission.is_completed:
            raise ValueError(
                "Apenas missões concluídas podem ser arquivadas."
            )

        cycle_id = self._normalize_identifier(
            mission.mission_id
        )

        cycle_path = (
            self.get_player_directory(puuid=puuid)
            / "history"
            / "training_cycles"
            / f"{cycle_id}.json"
        )

        if cycle_path.exists():
            return cycle_path

        data: dict[str, Any] = {
            "cycle_id": mission.mission_id,
            "archived_at": self._utc_now(),
            "status": "completed",
            "completion": {
                "games_completed": mission.games_completed,
                "games_target": mission.games_target,
                "progress_percentage": mission.progress_percentage,
                "is_completed": mission.is_completed,
            },
            "mission": mission.to_dict(),
        }

        self._write_json(
            path=cycle_path,
            data=data,
        )

        return cycle_path


    def save_training_cycle_evaluation(
        self,
        *,
        puuid: str,
        cycle_id: str,
        evaluation: dict[str, Any],
    ) -> Path:
        """
        Persiste a avaliação Before/After dentro de um ciclo arquivado.

        A operação atualiza apenas o campo `evaluation` e preserva
        missão, conclusão e metadados já existentes.
        """

        normalized_cycle_id = self._normalize_identifier(
            cycle_id
        )

        cycle_path = (
            self.get_player_directory(
                puuid=puuid,
            )
            / "history"
            / "training_cycles"
            / f"{normalized_cycle_id}.json"
        )

        data = self._read_json(
            path=cycle_path,
        )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Ciclo de treinamento não encontrado."
            )

        data["evaluation"] = {
            **evaluation,
            "evaluated_at": self._utc_now(),
        }

        self._write_json(
            path=cycle_path,
            data=data,
        )

        return cycle_path

    def load_training_cycle(
        self,
        *,
        puuid: str,
        cycle_id: str,
    ) -> dict[str, Any] | None:
        """Carrega um ciclo de treinamento já arquivado."""

        normalized_cycle_id = self._normalize_identifier(
            cycle_id
        )

        cycle_path = (
            self.get_player_directory(puuid=puuid)
            / "history"
            / "training_cycles"
            / f"{normalized_cycle_id}.json"
        )

        data = self._read_json(
            path=cycle_path,
        )

        if not isinstance(data, dict):
            return None

        return data

    def list_training_cycles(
        self,
        *,
        puuid: str,
    ) -> list[dict[str, Any]]:
        """Lista ciclos arquivados do mais recente para o mais antigo."""

        history_directory = (
            self.get_player_directory(puuid=puuid)
            / "history"
            / "training_cycles"
        )

        if not history_directory.exists():
            return []

        cycles: list[dict[str, Any]] = []

        for cycle_path in history_directory.glob("*.json"):
            data = self._read_json(
                path=cycle_path,
            )
            if isinstance(data, dict):
                cycles.append(data)

        cycles.sort(
            key=lambda item: str(
                item.get("archived_at", "")
            ),
            reverse=True,
        )

        return cycles

    def clear_training_mission(
        self,
        *,
        puuid: str,
    ) -> bool:
        """
        Remove a missão ativa do jogador.
        """

        mission_path = (
            self.get_player_directory(
                puuid=puuid,
            )
            / "training"
            / "current.json"
        )

        if not mission_path.exists():
            return False

        mission_path.unlink()

        return True

    def _save_profile(
        self,
        *,
        puuid: str,
        game_name: str,
        tag_line: str,
    ) -> None:
        """
        Cria ou atualiza o perfil persistente do jogador.
        """

        player_directory = self.get_player_directory(
            puuid=puuid,
        )

        profile_path = player_directory / "profile.json"

        existing_profile = self._read_json(
            profile_path
        )

        if not isinstance(existing_profile, dict):
            existing_profile = {}

        created_at = existing_profile.get(
            "created_at",
            self._utc_now(),
        )

        profile = {
            "puuid": puuid,
            "game_name": game_name.strip(),
            "tag_line": tag_line.strip(),
            "riot_id": (
                f"{game_name.strip()}#{tag_line.strip()}"
            ),
            "created_at": created_at,
            "updated_at": self._utc_now(),
            "last_analysis_at": existing_profile.get(
                "last_analysis_at"
            ),
            "last_benchmark_id": existing_profile.get(
                "last_benchmark_id"
            ),
        }

        self._write_json(
            path=profile_path,
            data=profile,
        )

    def _update_last_analysis(
        self,
        *,
        puuid: str,
        benchmark_id: str,
    ) -> None:
        """
        Atualiza informações da última análise no perfil.
        """

        profile_path = (
            self.get_player_directory(puuid=puuid)
            / "profile.json"
        )

        profile = self._read_json(profile_path)

        if not isinstance(profile, dict):
            return

        profile["last_analysis_at"] = self._utc_now()
        profile["last_benchmark_id"] = benchmark_id
        profile["updated_at"] = self._utc_now()

        self._write_json(
            path=profile_path,
            data=profile,
        )

    def _get_performance_path(
        self,
        *,
        puuid: str,
        benchmark_id: str,
    ) -> Path:
        normalized_benchmark_id = self._normalize_identifier(
            benchmark_id
        )

        player_directory = self.get_player_directory(
            puuid=puuid,
        )

        return (
            player_directory
            / "performance"
            / f"{normalized_benchmark_id}.json"
        )

    @staticmethod
    def _normalize_identifier(
        value: str,
    ) -> str:
        normalized = value.strip().lower()

        normalized = re.sub(
            r"[^a-z0-9_-]+",
            "_",
            normalized,
        )

        normalized = normalized.strip("_-")

        if not normalized:
            raise ValueError(
                "O identificador informado é inválido."
            )

        return normalized

    @staticmethod
    def _validate_puuid(
        puuid: str,
    ) -> None:
        if not puuid.strip():
            raise ValueError(
                "O PUUID do jogador não pode ser vazio."
            )

    @staticmethod
    def _read_json(
        path: Path,
    ) -> Any | None:
        if not path.exists():
            return None

        try:
            return json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return None

    @staticmethod
    def _write_json(
        *,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = json.dumps(
            data,
            ensure_ascii=False,
            indent=4,
        )

        temporary_path = path.with_suffix(
            path.suffix + ".tmp"
        )

        temporary_path.write_text(
            serialized,
            encoding="utf-8",
        )

        temporary_path.replace(path)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()