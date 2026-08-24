from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "fusion": ROOT / "src/coach/services/coach_context_fusion_service.py",
    "pipeline": ROOT / "src/coach/services/coach_pipeline_service.py",
    "route": ROOT / "src/integration_engine/api/routes/benchmark.py",
    "contract": ROOT / "src/integration_engine/contracts/benchmark.py",
    "page": ROOT / "partner_platform/pages/benchmark_page.py",
    "narrator": ROOT / "partner_platform/intelligence/local_coach_narrator.py",
}


def main() -> None:
    texts = {}

    for name, path in FILES.items():
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        texts[name] = text

    checks = [
        ("Fusion service existe", "class CoachContextFusionService" in texts["fusion"]),
        ("Fusion recebe Spectrum", "competitive_spectrum" in texts["fusion"]),
        ("Fusion recebe Learning Priority", "priority_plan" in texts["fusion"]),
        ("Fusion separa problema observado", '"problem_observed"' in texts["fusion"]),
        ("Fusion separa foco de treino", '"training_focus"' in texts["fusion"]),
        ("Fusion separa força a preservar", '"strength_to_preserve"' in texts["fusion"]),
        ("Fusion não altera prioridade", '"changes_learning_priority": False' in texts["fusion"]),
        ("Fusion não prevê subida", '"predicts_rank_up": False' in texts["fusion"]),
        (
            "Pipeline não passa Spectrum ao Priority Engine",
            "competitive_spectrum" not in (
                texts["pipeline"][
                    texts["pipeline"].find("LearningPriorityEngine.build("):
                    texts["pipeline"].find("LearningPriorityEngine.build(") + 500
                ]
                if "LearningPriorityEngine.build(" in texts["pipeline"]
                else ""
            ),
        ),
        ("Pipeline gera fusion após prioridade", "CoachContextFusionService.build" in texts["pipeline"]),
        ("API passa Spectrum ao pipeline", "competitive_spectrum=(" in texts["route"]),
        ("API expõe coach_fusion", 'comparison_data["coach_fusion"]' in texts["route"]),
        ("Contrato expõe coach_fusion", "coach_fusion: dict" in texts["contract"]),
        ("UI mostra Problema observado", "Problema observado" in texts["page"]),
        ("UI mostra Foco de treino", "Foco de treino" in texts["page"]),
        ("UI mostra Ponto forte a preservar", "Ponto forte a preservar" in texts["page"]),
        ("UI usa Contestação", '"Contestação"' in texts["page"]),
        ("UI traduz contest interno", "_public_coach_text" in texts["page"]),
        (
            "Prompt proíbe contest",
            'Nunca use a palavra interna "contest"' in texts["narrator"]
            and 'termo correto desta ferramenta é "contestação"' in texts["narrator"],
        ),
        ("Prompt exige contestação", '"contestação"' in texts["narrator"]),
        ("Spectrum não escolhe prioridade", "nunca pode substituir Learning Priority" in texts["narrator"]),
    ]

    print("=" * 86)
    print("TFT INSIGHT - COACH CONTEXT FUSION V1")
    print("=" * 86)

    passed = 0

    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 86)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("COACH CONTEXT FUSION V1: VALIDADO")
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
