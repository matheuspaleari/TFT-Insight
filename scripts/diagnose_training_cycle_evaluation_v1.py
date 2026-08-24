from __future__ import annotations

import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.benchmark import BenchmarkContextBuilder
from src.integration_engine.services.cached_match_service import CachedMatchService
from src.learning import SkillMappingService
from src.performance_engine.calculators import BenchmarkCalculator, PlayerMetricsCalculator
from src.performance_engine.collectors import BenchmarkCollector
from src.performance_engine.engine import BenchmarkEngine, PerformanceEngine
from src.riot_client import RiotClient
from src.storage import PlayerRepository
from src.training.services.training_cycle_evaluation_engine import TrainingCycleEvaluationEngine
from src.training.services.training_cycle_window_service import TrainingCycleWindowService
from src.training.services.training_metric_resolver import TrainingMetricResolver
from src.transformers.match_transformer import MatchTransformer


def _find_assessment(performance, skill_id: str):
    for assessment in SkillMappingService.assess(performance=performance):
        skill = getattr(assessment, "skill", None)
        candidate_id = (
            getattr(skill, "id", None)
            or getattr(assessment, "skill_id", None)
        )
        if candidate_id == skill_id:
            return assessment
    return None


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - TRAINING CYCLE EVALUATION V1 - REAL")
    print("=" * 82)

    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()
    benchmark_id = input("Benchmark ID [advanced]: ").strip() or "advanced"
    cycle_id = input("Cycle ID [mais recente]: ").strip()

    riot_client = RiotClient()
    loader = CachedMatchService(
        project_root=PROJECT_ROOT,
        riot_client=riot_client,
    )

    puuid = loader.resolve_puuid(
        puuid=None,
        game_name=game_name,
        tag_line=tag_line,
    )

    repository = PlayerRepository()
    cycles = repository.list_training_cycles(puuid=puuid)

    if not cycles:
        print("[ERRO] Nenhum ciclo concluído.")
        raise SystemExit(1)

    cycle = (
        next(
            (
                item
                for item in cycles
                if str(item.get("cycle_id", "")) == cycle_id
            ),
            None,
        )
        if cycle_id
        else cycles[0]
    )

    if cycle is None:
        print("[ERRO] Cycle ID não encontrado.")
        raise SystemExit(1)

    windows = TrainingCycleWindowService.reconstruct(
        puuid=puuid,
        cycle=cycle,
        cached_match_service=loader,
    )

    current_rank = riot_client.get_current_tft_tier(puuid=puuid) or "IRON"
    context = BenchmarkContextBuilder.build(current_rank=current_rank)

    metrics_calculator = PlayerMetricsCalculator()
    collector = BenchmarkCollector(
        riot_client=riot_client,
        match_transformer=MatchTransformer(),
        metrics_calculator=metrics_calculator,
        benchmark_calculator=BenchmarkCalculator(),
    )
    benchmark = BenchmarkEngine(collector=collector).load(
        benchmark_id=benchmark_id
    )

    before_metrics = metrics_calculator.calculate(
        matches=windows.before.load_result.matches
    )
    after_metrics = metrics_calculator.calculate(
        matches=windows.after.load_result.matches
    )

    weights = context.profile.performance_weights

    before_performance = PerformanceEngine.calculate(
        player_metrics=before_metrics,
        benchmark=benchmark,
        performance_weights=weights,
    )
    after_performance = PerformanceEngine.calculate(
        player_metrics=after_metrics,
        benchmark=benchmark,
        performance_weights=weights,
    )

    before_assessment = _find_assessment(
        before_performance,
        windows.skill_id,
    )
    after_assessment = _find_assessment(
        after_performance,
        windows.skill_id,
    )

    before_values = TrainingMetricResolver.resolve_many(
        player_metrics=before_metrics,
        metric_ids=windows.related_metric_ids,
    )
    after_values = TrainingMetricResolver.resolve_many(
        player_metrics=after_metrics,
        metric_ids=windows.related_metric_ids,
    )

    evaluation = TrainingCycleEvaluationEngine.evaluate(
        before_metrics=before_values,
        after_metrics=after_values,
        before_coverage=windows.before.coverage,
        after_coverage=windows.after.coverage,
        before_sample_size=windows.before.loaded_count,
        after_sample_size=windows.after.loaded_count,
    )

    print()
    print("=" * 82)
    print("RESULTADO DO CICLO")
    print("=" * 82)
    print(f"Cycle ID       : {windows.cycle_id}")
    print(f"Skill          : {windows.skill_id}")
    print(f"Exercício      : {windows.task_title}")
    print(f"Elo atual      : {current_rank}")
    print(f"Benchmark      : {benchmark_id}")
    print()
    print(f"Resultado      : {evaluation.result}")
    print(
        f"Confiança      : {evaluation.confidence} "
        f"({evaluation.confidence_score:.2f}%)"
    )
    print(
        "Sinais         : "
        f"+{evaluation.positive_metrics} / "
        f"={evaluation.stable_metrics} / "
        f"-{evaluation.negative_metrics}"
    )
    print(
        f"Métricas       : {evaluation.metrics_resolved}/"
        f"{evaluation.metrics_total}"
    )
    print(
        f"Cobertura      : BEFORE {evaluation.before_coverage:.2f}% | "
        f"AFTER {evaluation.after_coverage:.2f}%"
    )
    print(
        f"Amostras       : BEFORE {evaluation.before_sample_size} | "
        f"AFTER {evaluation.after_sample_size}"
    )

    print()
    print("-" * 82)
    print("MÉTRICAS")
    print("-" * 82)

    for item in evaluation.metric_evaluations:
        relative = (
            f"{item.relative_change * 100:+.2f}%"
            if item.relative_change is not None
            else "-"
        )
        print(
            f"{item.metric_id}: "
            f"{item.before:.4f} -> {item.after:.4f} | "
            f"delta {item.delta:+.4f} | "
            f"{relative} | {item.direction.upper()}"
        )

    print()
    print("-" * 82)
    print("SKILL ASSESSMENT - CONTEXTO AUXILIAR")
    print("-" * 82)

    before_score = getattr(before_assessment, "score", None)
    after_score = getattr(after_assessment, "score", None)

    print(f"BEFORE score : {before_score if before_score is not None else '-'}")
    print(f"AFTER score  : {after_score if after_score is not None else '-'}")
    print("Observação   : o SkillAssessment não decide a classificação do ciclo.")

    print()
    print("-" * 82)
    print("CONCLUSÃO DETERMINÍSTICA")
    print("-" * 82)
    print(evaluation.reason)
    print(evaluation.caveat)

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'RESULTADO DO CICLO' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
