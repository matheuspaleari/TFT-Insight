from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

load_dotenv(
    PROJECT_ROOT / ".env"
)


from partner_platform.services.api_client import DashboardApiClient
from src.learning import SkillMappingService
from src.learning.services.habit_engine import HabitEngine
from src.learning.services.habit_skill_mapping_service import (
    HabitSkillMappingService,
)
from src.learning.services.skill_evidence_fusion_service import (
    SkillEvidenceFusionService,
)
from src.learning.services.learning_priority_engine import (
    LearningPriorityEngine,
)
from src.services import PlayerAnalysisService


LEVEL_LABELS = {
    0: "Não avaliada",
    1: "Iniciante",
    2: "Em desenvolvimento",
    3: "Competente",
    4: "Avançada",
    5: "Dominada",
}

DECISION_LABELS = {
    "baseline_only": "Somente assessment oficial",
    "reinforced": "Assessment oficial reforçado pelo histórico",
    "evidence_disagreement": "Divergência entre assessment e histórico",
    "context_added": "Assessment preservado + contexto histórico",
    "context_only": "Somente contexto; continua não avaliada",
    "candidate_skill": "Skill candidata ao catálogo",
    "candidate_context": "Contexto de Skill candidata",
}


def _level_label(
    level,
) -> str:
    if level is None:
        return "-"

    return LEVEL_LABELS.get(
        int(level),
        str(level),
    )


def _format_optional(
    value,
    *,
    suffix: str = "",
) -> str:
    if value is None:
        return "-"

    if isinstance(value, float):
        return f"{value:.2f}{suffix}"

    return f"{value}{suffix}"


def main() -> None:
    print("=" * 82)
    print("TFT INSIGHT - REAL SKILL EVIDENCE FUSION DIAGNOSTIC")
    print("=" * 82)

    print()
    print(
        "Este diagnóstico usa o fluxo real do TFT Insight:"
    )
    print(
        "Performance -> SkillAssessment + coach_context -> Habits -> "
        "SkillSignals -> Evidence Fusion -> Learning Priority"
    )

    riot_id = input(
        "Riot ID (Game Name): "
    ).strip()

    tag = input(
        "Tag: "
    ).strip()

    benchmark_id = input(
        "Benchmark ID [advanced]: "
    ).strip() or "advanced"

    matches_raw = input(
        "Quantidade de partidas [30]: "
    ).strip() or "30"

    api_base_url = input(
        "API Base URL [http://127.0.0.1:8000]: "
    ).strip() or "http://127.0.0.1:8000"

    try:
        match_count = int(
            matches_raw
        )
    except ValueError:
        match_count = 30

    print()
    print("[1] Executando PlayerAnalysisService...")

    try:
        analysis = PlayerAnalysisService().analyze(
            game_name=riot_id,
            tag_line=tag,
            benchmark_id=benchmark_id,
            match_count=match_count,
            use_cache=True,
        )
    except Exception as exc:
        print(
            "[ERRO] Falha no PlayerAnalysisService:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print("[OK] Performance real recebida")
    print(
        f"Benchmark resolvido: {analysis.benchmark_id}"
    )
    print(
        f"Partidas válidas   : {len(analysis.match_ids)}"
    )

    print()
    print("[2] Gerando SkillAssessments oficiais...")

    try:
        assessments = SkillMappingService.assess(
            performance=analysis.performance
        )
    except Exception as exc:
        print(
            "[ERRO] Falha no SkillMappingService:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print(
        f"[OK] Assessments oficiais: {len(assessments)}"
    )

    print()
    print("[3] Buscando coach_context real...")

    client = DashboardApiClient(
        base_url=api_base_url,
        api_key=None,
    )

    try:
        comparison = client.compare_player_to_benchmark(
            benchmark_id=benchmark_id,
            game_name=riot_id,
            tag_line=tag,
            match_count=match_count,
        )
    except Exception as exc:
        print(
            "[ERRO] Falha ao buscar coach_context:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    coach_context = comparison.get(
        "coach_context"
    )

    if not coach_context:
        print(
            "[ERRO] coach_context não retornado."
        )
        return

    print("[OK] coach_context recebido")

    print()
    print("[4] Detectando Habits e SkillSignals...")

    habits = HabitEngine.detect(
        coach_context=coach_context
    )

    signals = HabitSkillMappingService.map(
        habits=habits
    )

    print(
        f"Habits       : {len(habits)}"
    )
    print(
        f"Skill Signals: {len(signals)}"
    )

    print()
    print("[5] Executando Skill Evidence Fusion...")

    fusion_results = SkillEvidenceFusionService.fuse(
        assessments=assessments,
        signals=signals,
    )

    print(
        f"[OK] Skills processadas: {len(fusion_results)}"
    )

    print()
    print("[6] Executando Learning Priority Engine...")

    try:
        plan = LearningPriorityEngine.build(
            fusion_results=tuple(fusion_results)
        )
    except Exception as exc:
        print(
            "[ERRO] Falha no Learning Priority Engine:"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return

    print("[OK] Learning Priority calculado")

    def print_priority(
        title: str,
        item,
    ) -> None:
        print()
        print("-" * 82)
        print(title)
        print("-" * 82)
        print(
            f"Skill ID       : {item.skill_id}"
        )
        print(
            f"Nome           : {item.skill_label}"
        )
        print(
            f"Confiança      : {item.confidence:.2f}%"
        )
        print(
            f"Evidência      : {item.evidence_status}"
        )
        print(
            f"Origem         : "
            + DECISION_LABELS.get(
                item.source_decision,
                item.source_decision,
            )
        )

        if item.habit_ids:
            print(
                "Habits         : "
                + ", ".join(
                    item.habit_ids
                )
            )

        print()
        print("Foco de treino:")
        print(
            item.training_focus
        )

        print()
        print("Motivo:")
        print(
            item.reason
        )

        if item.limitations:
            print()
            print("Limitações:")
            for limitation in item.limitations:
                print(
                    "  - "
                    + limitation
                )

    print()
    print("=" * 82)
    print("RESULTADO DO LEARNING PRIORITY")
    print("=" * 82)

    if plan.primary is not None:
        print_priority(
            "PRIORIDADE PRINCIPAL",
            plan.primary,
        )
    else:
        print()
        print(
            "PRIORIDADE PRINCIPAL: nenhuma"
        )

    for index, item in enumerate(
        plan.secondary,
        start=1,
    ):
        print_priority(
            f"PRIORIDADE SECUNDÁRIA {index}",
            item,
        )

    for index, item in enumerate(
        plan.strengths,
        start=1,
    ):
        print_priority(
            f"FORÇA A PRESERVAR {index}",
            item,
        )

    for index, item in enumerate(
        plan.context,
        start=1,
    ):
        print_priority(
            f"CONTEXTO {index}",
            item,
        )

    print()
    print("=" * 82)
    print("RESUMO")
    print("=" * 82)

    print(
        "Prioridade principal : "
        + (
            plan.primary.skill_id
            if plan.primary is not None
            else "-"
        )
    )

    print(
        "Secundárias          : "
        + (
            ", ".join(
                item.skill_id
                for item in plan.secondary
            )
            if plan.secondary
            else "-"
        )
    )

    print(
        "Forças               : "
        + (
            ", ".join(
                item.skill_id
                for item in plan.strengths
            )
            if plan.strengths
            else "-"
        )
    )

    print(
        "Contextos            : "
        + (
            ", ".join(
                item.skill_id
                for item in plan.context
            )
            if plan.context
            else "-"
        )
    )

    print()
    print(
        "Observação: scores internos de priorização "
        "não são exibidos."
    )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie o resultado da seção [6] até o final."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
