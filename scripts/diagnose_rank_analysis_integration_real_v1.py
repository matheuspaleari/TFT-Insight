from __future__ import annotations

import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.services import PlayerAnalysisService
from src.rank_history import RankObservationService


def main():
    print("=" * 82)
    print("TFT INSIGHT - RANK + PLAYER ANALYSIS INTEGRATION V1 - REAL")
    print("=" * 82)

    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()
    matches_raw = input("Quantidade de partidas [30]: ").strip() or "30"
    match_count = int(matches_raw)

    result = PlayerAnalysisService().analyze(
        game_name=game_name,
        tag_line=tag_line,
        match_count=match_count,
        use_cache=True,
    )

    history = RankObservationService.load_for_player(
        puuid=result.puuid
    )
    latest = (
        history.get("observations", [])[-1]
        if history.get("observations")
        else {}
    )

    print("\n" + "=" * 82)
    print("PLAYER ANALYSIS + RANK")
    print("=" * 82)
    print(f"Jogador              : {result.game_name}#{result.tag_line}")
    print(f"Elo exibido           : {result.current_rank}")
    print(f"Estágio competitivo   : {result.current_stage}")
    print(f"Próximo objetivo      : {result.target_stage}")
    print(f"Benchmark automático  : {result.benchmark_id}")
    print(f"Partidas da análise   : {len(result.match_ids)}")

    print("\n" + "=" * 82)
    print("RANK OBSERVATION")
    print("=" * 82)
    print(f"Tier                  : {latest.get('tier')}")
    print(f"Divisão               : {latest.get('division')}")
    print(f"LP                    : {latest.get('league_points')}")
    print(f"Última partida        : {latest.get('latest_match_id')}")
    print(
        "Partidas desde corte : "
        f"{latest.get('matches_since_previous_rank_snapshot')}"
    )
    print(f"Associação            : {latest.get('association')}")

    print("\n" + "=" * 82)
    print("VALIDAÇÃO ESPERADA PARA PINADOR DOSS#000")
    print("=" * 82)
    print("Elo exibido          : EMERALD IV · 0 LP")
    print("Benchmark automático : advanced")
    print("Estágio competitivo  : Avançado")
    print("Próximo objetivo     : EXPERT/Diamond conforme configuração atual")
    print()
    print("Se nenhuma nova partida foi jogada desde o BASELINE anterior,")
    print("o histórico NÃO deve criar um snapshot idêntico adicional.")

    print("\n" + "=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'PLAYER ANALYSIS + RANK' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
