from pathlib import Path
from statistics import mean
from typing import Any

from src.decision_engine import (
    CompositionHistoryAnalyzer,
    ContestHistoryAnalyzer,
    FlexHistoryAnalyzer,
)
from src.decision_engine.analyzers.strategic_decision_engine import (
    StrategicDecisionEngine,
)
from src.integration_engine.contracts import (
    AnalysisSignals,
    CompetitiveContext,
    AnalyzeRequest,
    IntegratedAnalysisResponse,
    CacheStatistics,
    LearningStatistics,
)
from src.integration_engine.adapters import (
    InternalReportAdapter,
)
from src.integration_engine.services.insight_engine import (
    InsightEngine,
)
from src.performance_engine.models import Match
from src.sprint1_engine import (
    KnowledgeLearningEngine,
    KnowledgeRepository,
)

from .item_classification_provider import (
    ItemClassificationProvider,
)


class InternalAnalysisPipeline:
    """
    Orquestra os motores internos e converte o resultado para o contrato B2B.
    """

    def __init__(
        self,
        *,
        project_root: Path,
        insight_engine: InsightEngine | None = None,
    ) -> None:
        self.project_root = project_root
        self.insight_engine = (
            insight_engine or InsightEngine()
        )
        self.item_provider = ItemClassificationProvider(
            project_root=project_root
        )
        self.knowledge_repository = KnowledgeRepository(
            project_root
            / "data"
            / "knowledge"
            / "tft_insight_knowledge.db"
        )

    def analyze_matches(
        self,
        *,
        matches: list[Match],
        payloads: list[dict[str, Any]],
        player_puuid: str,
        source: str,
        request_id: str | None,
        learn: bool,
        cache_statistics: CacheStatistics,
        competitive_context: CompetitiveContext | None = None,
    ) -> IntegratedAnalysisResponse:
        if not matches:
            raise ValueError(
                "Nenhuma partida válida foi fornecida."
            )

        classifications = self.item_provider.get()

        strategic = StrategicDecisionEngine.analyze(
            matches,
            item_classifications=classifications,
        )

        contest = ContestHistoryAnalyzer.analyze(
            matches
        )

        flex = FlexHistoryAnalyzer.analyze(
            matches,
            item_classifications=classifications,
        )

        composition = CompositionHistoryAnalyzer.analyze(
            matches,
            contest_history=contest,
            item_classifications=classifications,
        )

        patch, set_number = self._metadata(
            payloads
        )

        benchmark_score = self._benchmark_score(
            strategic_score=strategic.overall_score,
            average_placement=contest.average_placement,
        )

        signals = InternalReportAdapter.from_reports(
            strategic_report=strategic,
            contest_history=contest,
            flex_report=flex,
            benchmark_score=benchmark_score,
            sample_size=len(matches),
        )

        latest = contest.latest_report

        signal_data = signals.model_dump()

        signal_data.update(
            {
                "carry_contested": latest.carry_contested,
                "opponents_on_carry": (
                    latest.opponents_contesting_carry
                ),
            }
        )

        signals = AnalysisSignals(**signal_data)

        public_analysis = self.insight_engine.analyze(
            AnalyzeRequest(
                request_id=request_id,
                source=source,
                patch=patch,
                set_number=set_number,
                signals=signals,
            )
        )

        if competitive_context is not None:
            public_analysis = public_analysis.model_copy(
                update={
                    "competitive_context": competitive_context,
                    "current_rank": competitive_context.current_rank,
                    "current_stage": competitive_context.current_stage,
                    "target_stage": competitive_context.target_stage,
                    "profile_id": competitive_context.profile_id,
                    "benchmark_id": competitive_context.benchmark_id,
                }
            )

        learning_statistics = LearningStatistics(
            enabled=learn,
        )

        if learn:
            learning_result = self._learn(
                matches=matches,
                source=(
                    "challenger"
                    if source == "challenger"
                    else "player"
                ),
                patch=patch or "",
                set_number=set_number,
                contest=contest,
                composition=composition,
                payloads=payloads,
            )

            learning_statistics = LearningStatistics(
                enabled=True,
                inserted=learning_result.matches_inserted,
                reused=learning_result.matches_reused,
                observations_written=(
                    learning_result.observations_written
                ),
            )

        return IntegratedAnalysisResponse(
            analysis=public_analysis,
            cache=cache_statistics,
            learning=learning_statistics,
            player_puuid=player_puuid,
            matches_analyzed=len(matches),
            patch=patch,
            set_number=set_number,
            competitive_context=competitive_context,
        )

    def _learn(
        self,
        *,
        matches,
        source,
        patch,
        set_number,
        contest,
        composition,
        payloads,
    ):
        game_datetimes = {}

        for payload in payloads:
            metadata = payload.get("metadata", {})
            info = payload.get("info", {})
            match_id = str(
                metadata.get("match_id", "")
            )

            if match_id:
                value = info.get("game_datetime")
                if isinstance(value, int):
                    game_datetimes[match_id] = value

        contest_scores = {
            report.match_id: report.score
            for report in contest.match_reports
        }

        composition_keys = {
            snapshot.match_id: snapshot.composition_key
            for snapshot in composition.snapshots
        }

        return KnowledgeLearningEngine(
            self.knowledge_repository
        ).learn(
            matches=matches,
            source=source,
            patch=patch,
            set_number=set_number,
            game_datetimes=game_datetimes,
            contest_scores=contest_scores,
            composition_keys=composition_keys,
        )

    @staticmethod
    def _metadata(
        payloads: list[dict[str, Any]],
    ) -> tuple[str | None, int | None]:
        if not payloads:
            return None, None

        info = payloads[0].get("info", {})

        game_version = str(
            info.get("game_version", "")
        ).strip()

        patch = None

        if game_version:
            parts = game_version.split(".")
            patch = ".".join(parts[:2])

        raw_set = info.get("tft_set_number")
        set_number = (
            int(raw_set)
            if isinstance(raw_set, (int, float))
            else None
        )

        return patch, set_number

    @staticmethod
    def _benchmark_score(
        *,
        strategic_score: float,
        average_placement: float,
    ) -> float:
        placement_score = (
            100.0
            - (average_placement - 1.0)
            / 7.0
            * 100.0
        )

        return round(
            strategic_score * 0.55
            + placement_score * 0.45,
            2,
        )
