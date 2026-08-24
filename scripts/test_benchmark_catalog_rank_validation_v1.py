from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "catalog": ROOT / "src/benchmark/player_catalog.py",
    "rank": ROOT / "src/benchmark/rank_validation_service.py",
    "collector": ROOT / "src/performance_engine/collectors/benchmark_collector.py",
    "engine": ROOT / "src/performance_engine/engine/benchmark_engine.py",
    "validate": ROOT / "scripts/validate_benchmark_player_ranks_v1.py",
}
def main():
    texts={}
    for name,path in FILES.items():
        text=path.read_text(encoding="utf-8")
        ast.parse(text)
        texts[name]=text
    checks=[
        ("Catálogo individual existe","class BenchmarkPlayerCatalogEntry" in texts["catalog"]),
        ("Preserva tier at collection","tier_at_collection" in texts["catalog"]),
        ("Preserva current tier","current_tier" in texts["catalog"]),
        ("Preserva rank history","rank_history" in texts["catalog"]),
        ("Preserva métricas individuais","metrics:" in texts["catalog"]),
        ("Collector guarda catálogo","last_player_catalog" in texts["collector"]),
        ("Collector resolve Riot ID","get_account_by_puuid" in texts["collector"]),
        ("Collector preserva LP coleta","league_points_at_collection" in texts["collector"]),
        ("Engine salva catálogo","catalog_repository.save" in texts["engine"]),
        ("Validador consulta RANKED_TFT",'queue_type="RANKED_TFT"' in texts["rank"]),
        ("Validador detecta tier change","tier_changed" in texts["rank"]),
        ("Validador detecta division change","division_changed" in texts["rank"]),
        ("Validador detecta LP change","lp_changed" in texts["rank"]),
        ("Validador detecta saída do grupo","outside_group" in texts["rank"]),
        ("Script usa threshold de drift","--drift-threshold" in texts["validate"]),
        ("Gold I -> Gold IV não força rebuild","Gold I -> Gold IV" in texts["validate"]),
    ]
    passed=0
    print("="*82)
    print("TFT INSIGHT - BENCHMARK CATALOG + RANK VALIDATION V1")
    print("="*82)
    for i,(name,ok) in enumerate(checks,1):
        passed+=int(ok)
        print(f"\n[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")
    print("\n"+"="*82)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed==len(checks):
        print("BENCHMARK CATALOG + RANK VALIDATION V1: VALIDADO")
        raise SystemExit(0)
    raise SystemExit(1)
if __name__=="__main__":
    main()
