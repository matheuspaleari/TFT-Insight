from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.benchmark import BenchmarkContextBuilder

def main():
    page = (ROOT/"partner_platform/pages/benchmark_page.py").read_text(encoding="utf-8")
    builder = (ROOT/"src/benchmark/benchmark_context_builder.py").read_text(encoding="utf-8")
    checks = [
        ("Sem force challenger", 'benchmark_id = "challenger_br"' not in builder),
        ("Usa benchmark do grupo", "benchmark_id = group.benchmark_id" in builder),
        ("Emerald profile advanced", BenchmarkContextBuilder.build(current_rank="EMERALD").profile.id == "advanced"),
        ("Emerald benchmark advanced", BenchmarkContextBuilder.build(current_rank="EMERALD").benchmark_id == "advanced"),
        ("Contexto competitivo", '"Seu contexto competitivo"' in page),
        ("Explica referência", '"Por que esta referência?"' in page),
        ("Resultado primeiro", '"Resultado da comparação"' in page),
        ("Sem Percentil geral no topo", 'title="Percentil geral"' not in page),
        ("Áreas sob demanda", '"Ver as áreas comparadas"' in page),
        ("Mostra destaque", '"Seu destaque"' in page),
        ("Mostra oportunidade", '"Maior oportunidade"' in page),
        ("Mantém coach flutuante", "tft_coach_floating" in page),
        ("Mantém benchmark automático", "_analysis_benchmark_id" in page),
        ("Preserva LP", "leaguePoints" not in page or "LP" in page),
    ]
    print("="*82)
    print("TFT INSIGHT - P1.5 CONTEXTUAL ANALYSIS V1")
    print("="*82)
    passed=0
    for i,(name,ok) in enumerate(checks,1):
        passed += int(ok)
        print(f"\n[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")
    print("\n"+"="*82)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed == len(checks):
        print("P1.5 CONTEXTUAL ANALYSIS V1: VALIDADA")
        raise SystemExit(0)
    print("P1.5 CONTEXTUAL ANALYSIS V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)

if __name__ == "__main__":
    main()
