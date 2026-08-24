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
        "SkillSignals -> Evidence Fusion"
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

    for index, result in enumerate(
        fusion_results,
        start=1,
    ):
        print()
        print("-" * 82)
        print(
            f"SKILL FUSION {index}"
        )
        print("-" * 82)

        print(
            f"Skill ID          : {result.skill_id}"
        )
        print(
            f"Nome              : {result.skill_label}"
        )
        print(
            "Decisão           : "
            + DECISION_LABELS.get(
                result.decision,
                result.decision,
            )
        )

        print()
        print("Assessment oficial:")
        print(
            "  Existe           : "
            + (
                "Sim"
                if result.baseline_available
                else "Não"
            )
        )
        print(
            "  Nível            : "
            + _level_label(
                result.baseline_level
            )
        )
        print(
            "  Score            : "
            + _format_optional(
                result.baseline_score
            )
        )
        print(
            "  Confiança        : "
            + _format_optional(
                result.baseline_confidence,
                suffix="%",
            )
        )

        print()
        print("Resultado da fusão:")
        print(
            "  Nível            : "
            + _level_label(
                result.fused_level
            )
        )
        print(
            "  Score            : "
            + _format_optional(
                result.fused_score
            )
        )
        print(
            "  Confiança        : "
            + _format_optional(
                result.fused_confidence,
                suffix="%",
            )
        )

        if result.supporting_signals:
            print()
            print("SkillSignals relacionados:")

            for signal in result.supporting_signals:
                print(
                    "  - "
                    f"{signal.skill_id} | "
                    f"{signal.direction} | "
                    f"{signal.confidence:.2f}% | "
                    f"avaliável={'Sim' if signal.assessable else 'Não'} | "
                    f"nível={_level_label(signal.level_hint)}"
                )

                print(
                    "    Habits: "
                    + ", ".join(
                        signal.habit_ids
                    )
                )

        print()
        print("Interpretação:")
        print(
            result.interpretation
        )

        if result.limitations:
            print()
            print("Limitações:")
            for limitation in result.limitations:
                print(
                    "  - "
                    + limitation
                )

    print()
    print("=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print(
        "Envie todos os blocos SKILL FUSION."
    )
    print("=" * 82)


if __name__ == "__main__":
    main()
