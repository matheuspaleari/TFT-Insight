from __future__ import annotations

import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from partner_platform.services.api_client import DashboardApiClient
from src.learning import SkillMappingService
from src.learning.services.habit_engine import HabitEngine
from src.learning.services.habit_skill_mapping_service import HabitSkillMappingService
from src.learning.services.skill_evidence_fusion_service import SkillEvidenceFusionService
from src.learning.services.learning_priority_engine import LearningPriorityEngine
from src.services import PlayerAnalysisService
from src.training.services.training_plan_engine import TrainingPlanEngine


def show(values):
    if not values:
        print("-")
        return
    for value in values:
        print(f"- {value}")


def main():
    print("=" * 82)
    print("TFT INSIGHT - REAL TRAINING PLAN DIAGNOSTIC")
    print("=" * 82)
    print("\nEste diagnóstico usa o fluxo real do TFT Insight:")
    print("Performance -> SkillAssessment + coach_context -> Habits -> SkillSignals -> Evidence Fusion -> Learning Priority -> Training Plan")

    riot_id = input("Riot ID (Game Name): ").strip()
    tag = input("Tag: ").strip()
    benchmark_id = input("Benchmark ID [advanced]: ").strip() or "advanced"
    matches_raw = input("Quantidade de partidas [30]: ").strip() or "30"
    api_base_url = input("API Base URL [http://127.0.0.1:8000]: ").strip() or "http://127.0.0.1:8000"
    games_raw = input("Partidas no ciclo de treino [5]: ").strip() or "5"

    try:
        match_count = int(matches_raw)
    except ValueError:
        match_count = 30
    try:
        games_target = int(games_raw)
    except ValueError:
        games_target = 5

    print("\n[1] Executando PlayerAnalysisService...")
    try:
        analysis = PlayerAnalysisService().analyze(
            game_name=riot_id, tag_line=tag, benchmark_id=benchmark_id,
            match_count=match_count, use_cache=True,
        )
    except Exception as exc:
        print(f"[ERRO] PlayerAnalysisService: {type(exc).__name__}: {exc}")
        return
    print("[OK] Performance real recebida")
    print(f"Benchmark resolvido: {analysis.benchmark_id}")
    print(f"Partidas válidas   : {len(analysis.match_ids)}")

    print("\n[2] Gerando SkillAssessments oficiais...")
    try:
        assessments = SkillMappingService.assess(performance=analysis.performance)
    except Exception as exc:
        print(f"[ERRO] SkillMappingService: {type(exc).__name__}: {exc}")
        return
    print(f"[OK] Assessments oficiais: {len(assessments)}")

    print("\n[3] Buscando coach_context real...")
    client = DashboardApiClient(base_url=api_base_url, api_key=None)
    try:
        comparison = client.compare_player_to_benchmark(
            benchmark_id=benchmark_id, game_name=riot_id,
            tag_line=tag, match_count=match_count,
        )
    except Exception as exc:
        print(f"[ERRO] coach_context: {type(exc).__name__}: {exc}")
        return
    coach_context = comparison.get("coach_context")
    if not coach_context:
        print("[ERRO] coach_context não retornado.")
        return
    print("[OK] coach_context recebido")

    print("\n[4] Detectando Habits e SkillSignals...")
    habits = HabitEngine.detect(coach_context=coach_context)
    signals = HabitSkillMappingService.map(habits=habits)
    print(f"Habits       : {len(habits)}")
    print(f"Skill Signals: {len(signals)}")

    print("\n[5] Executando Skill Evidence Fusion...")
    try:
        fusion_results = SkillEvidenceFusionService.fuse(
            assessments=assessments, signals=signals,
        )
    except Exception as exc:
        print(f"[ERRO] Evidence Fusion: {type(exc).__name__}: {exc}")
        return
    print(f"[OK] Skills processadas: {len(fusion_results)}")

    print("\n[6] Executando Learning Priority Engine...")
    try:
        priority_plan = LearningPriorityEngine.build(
            fusion_results=tuple(fusion_results)
        )
    except Exception as exc:
        print(f"[ERRO] Learning Priority: {type(exc).__name__}: {exc}")
        return
    print("[OK] Learning Priority calculado")

    print("\n[7] Executando Training Plan Engine...")
    try:
        plan = TrainingPlanEngine.build(
            priority_plan=priority_plan, games_target=games_target,
        )
    except Exception as exc:
        print(f"[ERRO] Training Plan: {type(exc).__name__}: {exc}")
        return

    if plan is None:
        print("[OK] Nenhum plano criado: não existe prioridade oficial de treino.")
        return

    print("[OK] Training Plan calculado")
    print("\n" + "=" * 82)
    print("TRAINING PLAN REAL")
    print("=" * 82)

    print("\nPRIORIDADE")
    print(f"Skill       : {plan.primary_skill_label}")
    print(f"Skill ID    : {plan.primary_skill_id}")
    print(f"Confiança   : {plan.confidence:.2f}%")
    print(f"Ciclo       : {plan.games_target} partidas")

    print("\nOBJETIVO")
    print(plan.objective)

    print("\nPOR QUE ESTE FOCO")
    print(plan.rationale)

    print("\nEXERCÍCIO")
    print(plan.exercise.title)
    print("\n" + plan.exercise.instruction)

    print("\nCHECKLIST DURANTE O CICLO")
    show(plan.exercise.checklist)

    print("\nSINAIS DE SUCESSO")
    show(plan.exercise.success_signals)

    print("\nO QUE O TFT INSIGHT CONSEGUE VERIFICAR")
    print(plan.exercise.system_verification)

    print("\nFOCOS SECUNDÁRIOS")
    show(plan.secondary_focus)

    print("\nFORÇAS A PRESERVAR")
    show(plan.strengths_to_preserve)

    print("\nCONTEXTOS A OBSERVAR")
    show(plan.contexts_to_watch)

    if plan.limitations:
        print("\nLIMITAÇÕES DA PRIORIDADE PRINCIPAL")
        show(plan.limitations)

    print("\n" + "=" * 82)
    print("RESUMO DO CICLO")
    print("=" * 82)
    print(f"Treinar primeiro : {plan.primary_skill_label}")
    print(f"Exercício        : {plan.exercise.title}")
    print(f"Duração          : {plan.games_target} partidas")
    print(f"Verificação      : {plan.exercise.system_verification}")

    print("\nObservação: o plano foi escolhido por regras determinísticas; IA generativa não decidiu prioridade ou exercício.")
    print("\n" + "=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie o resultado da seção [7] até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
