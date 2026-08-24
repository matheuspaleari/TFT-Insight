from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "route": ROOT / "src/integration_engine/api/routes/integrated_analysis.py",
    "pipeline": ROOT / "src/integration_engine/services/internal_analysis_pipeline.py",
    "analysis": ROOT / "src/integration_engine/contracts/analysis.py",
    "internal": ROOT / "src/integration_engine/contracts/internal_analysis.py",
    "init": ROOT / "src/integration_engine/contracts/__init__.py",
}


def main():
    sources = {}
    for name, path in FILES.items():
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        sources[name] = text

    checks = [
        ("Contrato CompetitiveContext existe", "class CompetitiveContext" in sources["analysis"]),
        ("AnalyzeResponse recebe competitive_context", "competitive_context: CompetitiveContext | None" in sources["analysis"]),
        ("Compat current_rank existe", "current_rank: str | None" in sources["analysis"]),
        ("Compat benchmark_id existe", "benchmark_id: str | None" in sources["analysis"]),
        ("Integrated response expõe contexto", "competitive_context: CompetitiveContext | None" in sources["internal"]),
        ("CompetitiveContext exportado", '"CompetitiveContext"' in sources["init"]),
        ("Rota consulta RANKED_TFT", 'queue_type="RANKED_TFT"' in sources["route"]),
        ("Rota não usa Double Up", "RANKED_TFT_DOUBLE_UP" not in sources["route"]),
        ("Rota constrói BenchmarkContext", "BenchmarkContextBuilder.build" in sources["route"]),
        ("Rota preserva divisão", 'ranked_entry.get("rank"' in sources["route"]),
        ("Rota preserva LP", 'ranked_entry.get("leaguePoints"' in sources["route"]),
        ("Rota registra Rank Observation", ".record_resolved(" in sources["route"]),
        ("Pipeline recebe contexto", "competitive_context: CompetitiveContext | None" in sources["pipeline"]),
        ("Pipeline injeta contexto no analysis", '"current_rank": competitive_context.current_rank' in sources["pipeline"]),
        ("Pipeline injeta benchmark_id", '"benchmark_id": competitive_context.benchmark_id' in sources["pipeline"]),
        ("Pipeline devolve contexto top-level", "competitive_context=competitive_context" in sources["pipeline"]),
        ("Raw match continua sem exigir rank", "competitive_context: CompetitiveContext | None = None" in sources["pipeline"]),
    ]

    print("=" * 82)
    print("TFT INSIGHT - HOTFIX COMPETITIVE CONTEXT API V1")
    print("=" * 82)

    passed = 0
    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\n[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print("\n" + "=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("HOTFIX COMPETITIVE CONTEXT API V1: VALIDADO")
        raise SystemExit(0)

    print("HOTFIX COMPETITIVE CONTEXT API V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
