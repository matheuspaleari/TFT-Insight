from __future__ import annotations
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.learning.models.learning_priority import LearningPriority, LearningPriorityPlan
from src.training.services.training_plan_engine import TrainingPlanEngine

def item(skill_id, label, role, focus, confidence=80.0):
    return LearningPriority(skill_id, label, role, 1, 50.0, confidence, focus, "motivo", "official", "baseline_only", (), ())

def main():
    primary = item("consistency","Consistência","training","Aumentar a regularidade.")
    secondary = item("leveling","Leveling","training","Refinar ritmo e timing.",90.0)
    strength = item("board_pressure","Pressão de tabuleiro","strength","Preservar.",90.0)
    context = item("lobby_reading","Leitura de lobby","context","Observar.",78.0)
    plan = TrainingPlanEngine.build(priority_plan=LearningPriorityPlan(primary,(secondary,),(strength,),(context,)),games_target=5)
    tests = [
        ("Cria plano", plan is not None and plan.primary_skill_id=="consistency" and plan.games_target==5),
        ("Exercício acionável", plan.exercise.exercise_id=="consistency_decision_checkpoint" and len(plan.exercise.checklist)>=3),
        ("Secundária separada", len(plan.secondary_focus)==1),
        ("Força preservada", any("Pressão de tabuleiro" in x for x in plan.strengths_to_preserve)),
        ("Contexto não vira deficiência", any("sem transformar em deficiência" in x for x in plan.contexts_to_watch)),
        ("Sem prioridade = sem plano", TrainingPlanEngine.build(priority_plan=LearningPriorityPlan(None,(),(),())) is None),
    ]
    print("="*80)
    print("TFT INSIGHT - TRAINING PLAN V1 VALIDATION")
    print("="*80)
    passed=0
    for i,(name,ok) in enumerate(tests,1):
        passed += int(ok)
        print(f"\n[{i}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
    print("\n"+"="*80)
    print(f"PASSARAM: {passed}/{len(tests)}")
    print("TRAINING PLAN V1: VALIDADO" if passed==len(tests) else "TRAINING PLAN V1: AJUSTE NECESSÁRIO")
    raise SystemExit(0 if passed==len(tests) else 1)

if __name__ == "__main__":
    main()
