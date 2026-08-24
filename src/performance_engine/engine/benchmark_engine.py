"""
Engine responsável por persistir, carregar e atualizar benchmarks.
"""

import json
from pathlib import Path

from src.performance_engine.collectors import (
    BenchmarkCollector,
)
from src.performance_engine.models import Benchmark
from src.benchmark import BenchmarkPlayerCatalogRepository


class BenchmarkEngine:
    """
    Gerencia o ciclo de vida dos benchmarks persistidos.

    Cada benchmark possui um identificador próprio, permitindo
    manter referências diferentes por grupo competitivo.
    """

    DEFAULT_DIRECTORY = Path("data/benchmark")

    def __init__(
        self,
        collector: BenchmarkCollector,
        benchmark_directory: str | Path = DEFAULT_DIRECTORY,
    ) -> None:
        self.collector = collector
        self.benchmark_directory = Path(
            benchmark_directory
        )

        self.catalog_repository = (
            BenchmarkPlayerCatalogRepository(
                directory=self.benchmark_directory,
            )
        )

    def exists(
        self,
        benchmark_id: str,
    ) -> bool:
        """
        Verifica se um benchmark já está salvo.
        """

        return self._get_path(
            benchmark_id
        ).exists()

    def load(
        self,
        benchmark_id: str,
    ) -> Benchmark:
        """
        Carrega um benchmark salvo em JSON.
        """

        benchmark_path = self._get_path(
            benchmark_id
        )

        if not benchmark_path.exists():
            raise FileNotFoundError(
                "Benchmark não encontrado em: "
                f"{benchmark_path}"
            )

        try:
            raw_data = benchmark_path.read_text(
                encoding="utf-8",
            )

            data = json.loads(raw_data)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "O arquivo do benchmark contém "
                "um JSON inválido."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                "O arquivo do benchmark possui "
                "formato inválido."
            )

        return Benchmark.from_dict(data)

    def save(
        self,
        *,
        benchmark_id: str,
        benchmark: Benchmark,
    ) -> Path:
        """
        Salva um benchmark em JSON.
        """

        benchmark_path = self._get_path(
            benchmark_id
        )

        benchmark_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = json.dumps(
            benchmark.to_dict(),
            ensure_ascii=False,
            indent=4,
        )

        benchmark_path.write_text(
            serialized,
            encoding="utf-8",
        )

        return benchmark_path

    def load_or_collect(
        self,
        *,
        benchmark_id: str,
        queue: str = "RANKED_TFT",
        minimum_valid_matches: int | None = None,
    ) -> Benchmark:
        """
        Carrega o benchmark salvo ou realiza sua coleta.
        """

        if self.exists(benchmark_id):
            print(
                f"Benchmark '{benchmark_id}' já existente. "
                "Carregando arquivo salvo..."
            )

            return self.load(benchmark_id)

        print(
            f"Benchmark '{benchmark_id}' não encontrado. "
            "Coletando dados da Riot API..."
        )

        return self.refresh(
            benchmark_id=benchmark_id,
            queue=queue,
            minimum_valid_matches=(
                minimum_valid_matches
            ),
        )

    def refresh(
        self,
        *,
        benchmark_id: str,
        queue: str = "RANKED_TFT",
        minimum_valid_matches: int | None = None,
    ) -> Benchmark:
        """
        Força a coleta e substitui o benchmark persistido.
        """

        benchmark = self.collector.collect(
            benchmark_id=benchmark_id,
            queue=queue,
            minimum_valid_matches=(
                minimum_valid_matches
            ),
        )

        benchmark_path = self.save(
            benchmark_id=benchmark_id,
            benchmark=benchmark,
        )

        catalog_path = None
        catalog = getattr(
            self.collector,
            "last_player_catalog",
            [],
        )

        if catalog:
            catalog_path = self.catalog_repository.save(
                benchmark_id=benchmark_id,
                players=catalog,
            )

        print(
            "Benchmark atualizado e salvo em: "
            f"{benchmark_path}"
        )

        if catalog_path is not None:
            print(
                "Catálogo individual salvo em: "
                f"{catalog_path}"
            )

        return benchmark

    def list_available(self) -> list[str]:
        """
        Lista os identificadores dos benchmarks salvos.
        """

        if not self.benchmark_directory.exists():
            return []

        return sorted(
            path.stem
            for path in self.benchmark_directory.glob(
                "*.json"
            )
            if path.is_file()
        )

    def _get_path(
        self,
        benchmark_id: str,
    ) -> Path:
        """
        Monta o caminho de um benchmark.
        """

        normalized_id = self._normalize_id(
            benchmark_id
        )

        return (
            self.benchmark_directory
            / f"{normalized_id}.json"
        )

    @staticmethod
    def _normalize_id(
        benchmark_id: str,
    ) -> str:
        """
        Normaliza e valida o identificador.
        """

        normalized_id = (
            benchmark_id.strip().lower()
        )

        if not normalized_id:
            raise ValueError(
                "O identificador do benchmark "
                "não pode ser vazio."
            )

        if not all(
            character.isalnum()
            or character in {"_", "-"}
            for character in normalized_id
        ):
            raise ValueError(
                "O identificador do benchmark deve "
                "conter apenas letras, números, "
                "hífen ou underline."
            )

        return normalized_id
