from __future__ import annotations
from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.services import PlayerAnalysisService

def main():
    print("=" * 88)
    print("TFT INSIGHT - COMPETITIVE SPECTRUM ENGINE V1 - REAL")
    print("=" * 88)
    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()
    match_count = int(input("Partidas [30]: ").strip() or "30")

    result = PlayerAnalysisService().analyze(
        game_name=game_name,
        tag_line=tag_line,
        match_count=match_count,
        use_cache=True,
    )
    spectrum = result.competitive_spectrum or {}

    print("\n" + "=" * 88)
    print("COMPETITIVE SPECTRUM")
    print("=" * 88)
    print(f"Jogador              : {result.riot_id}")
    print(f"Elo atual            : {result.current_rank}")
    print(f"Grupo competitivo    : {result.current_stage}")
    print(f"Benchmark            : {result.benchmark_id}")
    print(f"Disponível           : {'Sim' if spectrum.get('available') else 'Não'}")
    if spectrum.get("available"):
        print(f"Posição teórica      : {spectrum['spectrum_position'] * 100:.1f}%")
        print(f"Percentil no grupo   : {spectrum['spectrum_percentile'] * 100:.1f}%")
        print(f"Faixa                : {spectrum['spectrum_band']}")
        print(f"População comparada  : {spectrum['population_size']}")
    else:
        print(f"Limitação            : {spectrum.get('limitation', '-')}")

    print("\nPERFIL COMPARATIVO")
    print("-" * 88)
    for item in spectrum.get("performance_profile", []):
        print(
            f"{item['metric']:<34} score={item['score']:>6.2f} "
            f"| {item['classification']}"
        )

    print("\nRESUMO")
    print("-" * 88)
    print("Forças               : " + (", ".join(spectrum.get("strengths", [])) or "-"))
    print("Dentro do padrão     : " + (", ".join(spectrum.get("neutral_areas", [])) or "-"))
    print("Pontos de atenção    : " + (", ".join(spectrum.get("attention_areas", [])) or "-"))

    print("\n" + "=" * 88)
    print("PROTEÇÕES")
    print("=" * 88)
    print("Não estima probabilidade de subir.")
    print("Não declara que o jogador está pronto para subir.")
    print("Não usa X/Y métricas como requisito de promoção.")
    print("Não altera Learning Priority, missão ou dificuldade.")
    print("\n" + "=" * 88)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'COMPETITIVE SPECTRUM' até o final.")
    print("=" * 88)

if __name__ == "__main__":
    main()
