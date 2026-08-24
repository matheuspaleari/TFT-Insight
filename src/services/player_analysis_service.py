"""
Serviço principal para análise de jogadores.
"""

import hashlib
import json

from src.benchmark import (
    BenchmarkContext,
    BenchmarkContextBuilder,
    CompetitiveSpectrumEngine,
)
from src.performance_engine.calculators import (
    BenchmarkCalculator,
    PlayerMetricsCalculator,
)
from src.performance_engine.collectors import BenchmarkCollector
from src.performance_engine.engine import (
    BenchmarkEngine,
    PerformanceEngine,
)
from src.performance_engine.models import (
    Benchmark,
    PlayerAnalysisResult,
)
from src.riot_client import RiotClient
from src.rank_history import RankObservationService
from src.storage import PlayerRepository
from src.transformers.match_transformer import MatchTransformer


class PlayerAnalysisService:
    """
    Coordena a análise completa de um jogador.

    Responsabilidades:

    - buscar a conta Riot;
    - identificar o elo atual do jogador;
    - construir o contexto competitivo;
    - criar ou atualizar o diretório persistente do jogador;
    - buscar as partidas recentes;
    - carregar o benchmark persistido;
    - utilizar os pesos do perfil competitivo;
    - reutilizar uma Performance persistida quando válida;
    - processar novas partidas quando necessário;
    - persistir o resultado no PlayerRepository;
    - retornar um PlayerAnalysisResult completo.
    """

    DEFAULT_MATCH_COUNT = 20

    def __init__(
        self,
        riot_client: RiotClient | None = None,
        match_transformer: MatchTransformer | None = None,
        metrics_calculator: PlayerMetricsCalculator | None = None,
        benchmark_engine: BenchmarkEngine | None = None,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.riot_client = riot_client or RiotClient()

        self.match_transformer = (
            match_transformer
            or MatchTransformer()
        )

        self.metrics_calculator = (
            metrics_calculator
            or PlayerMetricsCalculator()
        )

        self.player_repository = (
            player_repository
            or PlayerRepository()
        )

        if benchmark_engine is not None:
            self.benchmark_engine = benchmark_engine
        else:
            collector = BenchmarkCollector(
                riot_client=self.riot_client,
                match_transformer=self.match_transformer,
                metrics_calculator=self.metrics_calculator,
                benchmark_calculator=BenchmarkCalculator(),
            )

            self.benchmark_engine = BenchmarkEngine(
                collector=collector,
            )

        self.competitive_spectrum_engine = (
            CompetitiveSpectrumEngine()
        )

    def analyze(
        self,
        *,
        game_name: str,
        tag_line: str,
        benchmark_id: str | None = None,
        match_count: int = DEFAULT_MATCH_COUNT,
        use_cache: bool = True,
    ) -> PlayerAnalysisResult:
        """
        Executa a análise completa de um jogador.

        O benchmark é escolhido automaticamente pelo contexto
        competitivo do jogador.

        O parâmetro benchmark_id pode ser usado como substituição
        manual durante testes.

        Quando use_cache=True, reutiliza uma Performance persistida
        caso as partidas, o benchmark, o contexto competitivo e os
        pesos continuem iguais.
        """

        self._validate_parameters(
            game_name=game_name,
            tag_line=tag_line,
            match_count=match_count,
        )

        account = self.riot_client.get_account(
            game_name=game_name,
            tag_line=tag_line,
        )

        player_puuid = account.get("puuid")

        if not isinstance(player_puuid, str) or not player_puuid:
            raise RuntimeError(
                "A Riot API não retornou um PUUID válido."
            )

        account_game_name = str(
            account.get(
                "gameName",
                game_name,
            )
        )

        account_tag_line = str(
            account.get(
                "tagLine",
                tag_line,
            )
        )

        ranked_entry = (
            self.riot_client.get_ranked_tft_entry(
                puuid=player_puuid,
                queue_type="RANKED_TFT",
            )
        )

        current_tier = self._rank_tier(
            ranked_entry
        )

        if current_tier is None:
            print(
                "Jogador sem elo ranqueado. "
                "Utilizando o estágio Fundamentos."
            )
            benchmark_tier = "IRON"
            current_rank_display = "Não ranqueado"
        else:
            benchmark_tier = current_tier
            current_rank_display = (
                self._format_rank_display(
                    ranked_entry
                )
            )

        benchmark_context = (
            BenchmarkContextBuilder.build(
                current_rank=benchmark_tier,
            )
        )

        resolved_benchmark_id = (
            benchmark_id
            or benchmark_context.benchmark_id
        )

        target_display_name = (
            benchmark_context.group.target_stage
        )

        print(
            "Contexto competitivo: "
            f"{benchmark_context.group.display_name} "
            f"→ {target_display_name}"
        )

        print(
            "Benchmark utilizado: "
            f"{resolved_benchmark_id}"
        )

        print(
            "Perfil competitivo: "
            f"{benchmark_context.profile.id}"
        )

        player_directory = (
            self.player_repository.ensure_player(
                puuid=player_puuid,
                game_name=account_game_name,
                tag_line=account_tag_line,
            )
        )

        print(
            "Diretório do jogador: "
            f"{player_directory}"
        )

        rank_scan_limit = max(
            match_count,
            RankObservationService.DEFAULT_SCAN_LIMIT,
        )

        recent_match_ids = self.riot_client.get_match_ids(
            puuid=player_puuid,
            count=rank_scan_limit,
        )

        match_ids = recent_match_ids[:match_count]

        if not match_ids:
            raise RuntimeError(
                "Nenhuma partida recente foi encontrada."
            )

        rank_observation = (
            RankObservationService(
                riot_client=self.riot_client,
                player_repository=self.player_repository,
            ).record_resolved(
                puuid=player_puuid,
                game_name=account_game_name,
                tag_line=account_tag_line,
                ranked_entry=ranked_entry,
                current_match_ids=recent_match_ids,
                scan_limit=rank_scan_limit,
            )
        )

        observation = rank_observation.get(
            "observation",
            {}
        )

        print(
            "Elo observado: "
            f"{current_rank_display}"
        )
        print(
            "Partidas desde snapshot de elo: "
            f"{observation.get('matches_since_previous_rank_snapshot', 0)}"
        )
        print(
            "Associação de elo: "
            f"{observation.get('association', '-')}"
        )

        benchmark = self.benchmark_engine.load(
            benchmark_id=resolved_benchmark_id,
        )

        performance_weights = (
            benchmark_context
            .profile
            .performance_weights
        )

        analysis_fingerprint = (
            self._build_analysis_fingerprint(
                benchmark=benchmark,
                benchmark_context=benchmark_context,
                resolved_benchmark_id=(
                    resolved_benchmark_id
                ),
            )
        )

        if use_cache:
            stored_performance = (
                self.player_repository.load_performance(
                    puuid=player_puuid,
                    benchmark_id=resolved_benchmark_id,
                    match_ids=match_ids,
                    benchmark_fingerprint=(
                        analysis_fingerprint
                    ),
                )
            )

            if stored_performance is not None:
                print(
                    "Análise persistida encontrada. "
                    "Reutilizando a Performance do jogador..."
                )

                spectrum = self._competitive_spectrum(
                    benchmark_id=resolved_benchmark_id,
                    benchmark_context=benchmark_context,
                    ranked_entry=ranked_entry,
                    current_rank=current_rank_display,
                    performance=stored_performance,
                )

                return PlayerAnalysisResult(
                    puuid=player_puuid,
                    game_name=account_game_name,
                    tag_line=account_tag_line,
                    current_rank=current_rank_display,
                    current_stage=(
                        benchmark_context.group.display_name
                    ),
                    target_stage=target_display_name,
                    profile_id=benchmark_context.profile.id,
                    benchmark_id=resolved_benchmark_id,
                    match_ids=tuple(match_ids),
                    performance=stored_performance,
                    competitive_spectrum=spectrum.to_dict(),
                )

        print(
            "Análise persistida não encontrada "
            "ou desatualizada. Processando partidas..."
        )

        transformed_matches = []

        for index, match_id in enumerate(
            match_ids,
            start=1,
        ):
            print(
                f"Processando partida "
                f"{index}/{len(match_ids)}..."
            )

            try:
                match_data = (
                    self.riot_client.get_match_details(
                        match_id=match_id,
                    )
                )

                transformed_match = (
                    self.match_transformer.transform(
                        match_data,
                        player_puuid,
                    )
                )

                transformed_matches.append(
                    transformed_match
                )

            except (
                RuntimeError,
                ValueError,
                KeyError,
            ) as error:
                print(
                    f"Partida {match_id} ignorada: "
                    f"{error}"
                )

        if not transformed_matches:
            raise RuntimeError(
                "Nenhuma partida válida pôde ser processada."
            )

        player_metrics = (
            self.metrics_calculator.calculate(
                matches=transformed_matches,
            )
        )

        performance = PerformanceEngine.calculate(
            player_metrics=player_metrics,
            benchmark=benchmark,
            performance_weights=performance_weights,
        )

        if use_cache:
            performance_path = (
                self.player_repository.save_performance(
                    puuid=player_puuid,
                    benchmark_id=resolved_benchmark_id,
                    benchmark_fingerprint=(
                        analysis_fingerprint
                    ),
                    match_ids=match_ids,
                    performance=performance,
                )
            )

            print(
                "Performance persistida em: "
                f"{performance_path}"
            )

        spectrum = self._competitive_spectrum(
            benchmark_id=resolved_benchmark_id,
            benchmark_context=benchmark_context,
            ranked_entry=ranked_entry,
            current_rank=current_rank_display,
            performance=performance,
        )

        return PlayerAnalysisResult(
            puuid=player_puuid,
            game_name=account_game_name,
            tag_line=account_tag_line,
            current_rank=current_rank_display,
            current_stage=(
                benchmark_context.group.display_name
            ),
            target_stage=target_display_name,
            profile_id=benchmark_context.profile.id,
            benchmark_id=resolved_benchmark_id,
            match_ids=tuple(match_ids),
            performance=performance,
            competitive_spectrum=spectrum.to_dict(),
        )

    def _competitive_spectrum(
        self,
        *,
        benchmark_id: str,
        benchmark_context: BenchmarkContext,
        ranked_entry: dict | None,
        current_rank: str,
        performance,
    ):
        tier = None
        division = None
        league_points = None

        if isinstance(ranked_entry, dict):
            raw_tier = ranked_entry.get("tier")
            raw_division = ranked_entry.get("rank")
            raw_lp = ranked_entry.get("leaguePoints")

            if isinstance(raw_tier, str):
                tier = raw_tier.strip().upper() or None
            if isinstance(raw_division, str):
                division = raw_division.strip().upper() or None
            if isinstance(raw_lp, int):
                league_points = raw_lp

        return self.competitive_spectrum_engine.analyze(
            benchmark_id=benchmark_id,
            group_label=benchmark_context.group.display_name,
            tier=tier,
            division=division,
            league_points=league_points,
            current_rank=current_rank,
            performance=performance,
        )

    @staticmethod
    def _rank_tier(
        entry: dict | None,
    ) -> str | None:
        if not isinstance(entry, dict):
            return None

        tier = entry.get("tier")
        if not isinstance(tier, str):
            return None

        normalized = tier.strip().upper()
        return normalized or None

    @staticmethod
    def _format_rank_display(
        entry: dict | None,
    ) -> str:
        if not isinstance(entry, dict):
            return "Não ranqueado"

        tier = str(
            entry.get("tier", "")
        ).strip().upper()
        division = str(
            entry.get("rank", "")
        ).strip().upper()
        lp = entry.get("leaguePoints")

        if not tier:
            return "Não ranqueado"

        parts = [tier]
        if division:
            parts.append(division)

        rank_text = " ".join(parts)

        if isinstance(lp, int):
            rank_text += f" · {lp} LP"

        return rank_text

    @staticmethod
    def _build_analysis_fingerprint(
        *,
        benchmark: Benchmark,
        benchmark_context: BenchmarkContext,
        resolved_benchmark_id: str,
    ) -> str:
        """
        Gera uma assinatura estável da configuração da análise.

        A assinatura considera:

        - o conteúdo do benchmark;
        - o benchmark físico utilizado;
        - o elo atual;
        - o grupo competitivo;
        - o perfil competitivo;
        - os pesos de Performance.

        Dessa forma, o cache é invalidado quando qualquer parte
        relevante da configuração da análise muda.
        """

        serialized_weights = {
            metric.value: weight
            for metric, weight
            in (
                benchmark_context
                .profile
                .performance_weights
                .items()
            )
        }

        serialized = json.dumps(
            {
                "benchmark": benchmark.to_dict(),
                "competitive_context": {
                    "current_rank": (
                        benchmark_context.current_rank
                    ),
                    "group_id": (
                        benchmark_context.group.id
                    ),
                    "group_display_name": (
                        benchmark_context
                        .group
                        .display_name
                    ),
                    "target_stage": (
                        benchmark_context
                        .group
                        .target_stage
                    ),
                    "profile_id": (
                        benchmark_context.profile.id
                    ),
                    "configured_benchmark_id": (
                        benchmark_context.benchmark_id
                    ),
                    "resolved_benchmark_id": (
                        resolved_benchmark_id
                    ),
                    "performance_weights": (
                        serialized_weights
                    ),
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _validate_parameters(
        *,
        game_name: str,
        tag_line: str,
        match_count: int,
    ) -> None:
        """
        Valida os dados de entrada da análise.
        """

        if not game_name.strip():
            raise ValueError(
                "O nome do jogador deve ser informado."
            )

        if not tag_line.strip():
            raise ValueError(
                "A tag do jogador deve ser informada."
            )

        if match_count < 1:
            raise ValueError(
                "A quantidade de partidas deve ser maior que zero."
            )