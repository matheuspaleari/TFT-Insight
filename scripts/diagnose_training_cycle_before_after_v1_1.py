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
from src.training.services.training_cycle_window_service import TrainingCycleWindowService
from src.training.services.training_metric_resolver import TrainingMetricResolver
from src.transformers.match_transformer import MatchTransformer


LEVEL_LABELS = {
    0: "Não avaliada",
    1: "Iniciante",
    2: "Em desenvolvimento",
    3: "Competente",
    4: "Avançada",
    5: "Dominada",
}

METRIC_LABELS = {
    "average_level": "Nível médio",
    "average_damage_to_players": "Dano médio a jogadores",
    "average_players_eliminated": "Jogadores eliminados em média",
    "placement_standard_deviation": "Desvio de colocação",
    "average_gold_left": "Ouro restante médio",
}


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


def _level_text(value) -> str:
    if value is None:
        return "-"
    try:
        return LEVEL_LABELS.get(int(value), str(value))
    except (TypeError, ValueError):
        return str(value)


def _number(value) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.4f}"
    return "-"


def _show_window(title, window, assessment, resolved_metrics):
    print()
    print("-" * 82)
    print(title)
    print("-" * 82)
    print(f"Partidas solicitadas : {window.requested_count}")
    print(f"Partidas carregadas  : {window.loaded_count}")
    print(f"Cobertura             : {window.coverage:.2f}%")
    print(f"Cache utilizado       : {window.load_result.cached_matches_used}")
    print(f"Baixadas da Riot      : {window.load_result.new_matches_downloaded}")
    print(f"Falhas                : {window.load_result.failed_matches}")

    level = getattr(assessment, "level", None) if assessment else None
    score = getattr(assessment, "score", None) if assessment else None
    confidence = getattr(assessment, "confidence", None) if assessment else None

    print()
    print("SkillAssessment:")
    print(f"  Nível      : {_level_text(level)}")
    print(f"  Score      : {_number(score)}")
    print(
        "  Confiança  : "
        + (
            f"{float(confidence):.2f}%"
            if isinstance(confidence, (int, float))
            else "-"
        )
    )

    print()
    print("Métricas relacionadas à missão:")
    for metric_id, value in resolved_metrics.items():
        label = METRIC_LABELS.get(metric_id, metric_id)
        print(f"  {label} ({metric_id}): {_number(value)}")


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - BEFORE/AFTER RECONSTRUCTION V1.1")
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
        print("[ERRO] Nenhum ciclo concluído foi encontrado.")
        raise SystemExit(1)

    if cycle_id:
        cycle = next(
            (
                item
                for item in cycles
                if str(item.get("cycle_id", "")) == cycle_id
            ),
            None,
        )
        if cycle is None:
            print("[ERRO] Cycle ID não encontrado.")
            raise SystemExit(1)
    else:
        cycle = cycles[0]

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
    benchmark_engine = BenchmarkEngine(collector=collector)
    benchmark = benchmark_engine.load(benchmark_id=benchmark_id)
    weights = context.profile.performance_weights

    before_metrics = metrics_calculator.calculate(
        matches=windows.before.load_result.matches
    )
    after_metrics = metrics_calculator.calculate(
        matches=windows.after.load_result.matches
    )

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

    print()
    print("=" * 82)
    print("CICLO RECONSTRUÍDO V1.1")
    print("=" * 82)
    print(f"Cycle ID    : {windows.cycle_id}")
    print(f"Skill       : {windows.skill_id}")
    print(f"Task        : {windows.task_title}")
    print(f"Task ID     : {windows.task_id}")
    print(f"Elo atual   : {current_rank}")
    print(f"Benchmark   : {benchmark_id}")

    _show_window(
        "BEFORE - BASELINE DA MISSÃO",
        windows.before,
        before_assessment,
        before_values,
    )

    _show_window(
        "AFTER - PARTIDAS DO CICLO",
        windows.after,
        after_assessment,
        after_values,
    )

    print()
    print("-" * 82)
    print("DELTA OBSERVADO - AFTER MENOS BEFORE")
    print("-" * 82)

    resolved = 0

    for metric_id in windows.related_metric_ids:
        before = before_values.get(metric_id)
        after = after_values.get(metric_id)
        delta = TrainingMetricResolver.delta(
            before=before,
            after=after,
        )

        label = METRIC_LABELS.get(metric_id, metric_id)
        print(
            f"{label}: "
            f"{_number(before)} -> {_number(after)} "
            f"| delta {_number(delta)}"
        )

        if delta is not None:
            resolved += 1

    print()
    print(
        f"Métricas resolvidas: {resolved}/"
        f"{len(windows.related_metric_ids)}"
    )

    print()
    print("=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print("O delta é apenas uma diferença observada entre as janelas.")
    print("Esta etapa ainda NÃO classifica melhora, estabilidade ou piora.")
    print("O SkillAssessment AFTER continua sendo contexto auxiliar.")
    print(
        "A amostra AFTER é menor que a BEFORE e será tratada "
        "com confiança conservadora."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'CICLO RECONSTRUÍDO V1.1' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
