from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "engine": ROOT / "src/benchmark/competitive_spectrum_engine.py",
    "service": ROOT / "src/services/player_analysis_service.py",
    "model": ROOT / "src/performance_engine/models/player_analysis_result.py",
    "contract": ROOT / "src/integration_engine/contracts/analysis.py",
    "route": ROOT / "src/integration_engine/api/routes/integrated_analysis.py",
}

def main():
    texts = {}
    for name, path in FILES.items():
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        texts[name] = text

    checks = [
        ("Engine existe", "class CompetitiveSpectrumEngine" in texts["engine"]),
        ("Resultado possui percentil", "spectrum_percentile" in texts["engine"]),
        ("Resultado possui faixa", "spectrum_band" in texts["engine"]),
        ("Usa catálogo individual", "BenchmarkPlayerCatalogRepository" in texts["engine"]),
        ("Usa elo/divisão/LP", "rank_sort_key" in texts["engine"]),
        ("Perfil separa força", '"STRENGTH"' in texts["engine"]),
        ("Perfil separa neutro", '"NEUTRAL"' in texts["engine"]),
        ("Perfil separa atenção", '"ATTENTION"' in texts["engine"]),
        ("PlayerAnalysisResult transporta Spectrum", "competitive_spectrum" in texts["model"]),
        ("PlayerAnalysisService integra Spectrum", "_competitive_spectrum" in texts["service"]),
        ("Cache também recebe Spectrum", "performance=stored_performance" in texts["service"]),
        ("Contrato API possui Spectrum", "class CompetitiveSpectrum(BaseModel)" in texts["contract"]),
        ("CompetitiveContext expõe Spectrum", "spectrum: CompetitiveSpectrum" in texts["contract"]),
        ("Rota integrada calcula Spectrum", "CompetitiveSpectrumEngine" in texts["route"]),
        ("Sem probability_to_rank_up", "probability_to_rank_up" not in texts["engine"]),
        ("Sem ready_to_rank_up", "ready_to_rank_up" not in texts["engine"]),
        ("Sem metrics_needed_to_rank_up", "metrics_needed_to_rank_up" not in texts["engine"]),
        ("Sem pesos de correlação", "progression_signal" not in texts["engine"]),
    ]

    print("=" * 84)
    print("TFT INSIGHT - COMPETITIVE SPECTRUM ENGINE V1")
    print("=" * 84)
    passed = 0
    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\n[{index}] {name}\nStatus  : {'OK' if ok else 'ERRO'}")
    print("\n" + "=" * 84)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed == len(checks):
        print("COMPETITIVE SPECTRUM ENGINE V1: VALIDADO")
        raise SystemExit(0)
    raise SystemExit(1)

if __name__ == "__main__":
    main()
