from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.rank_history import RankObservationService


def rank_text(obs):
    if not obs.get("ranked"):
        return "Não ranqueado"
    tier = obs.get("tier") or "-"
    division = obs.get("division") or ""
    lp = obs.get("league_points")
    lp_text = f"{lp} LP" if lp is not None else "LP -"
    return f"{tier} {division} · {lp_text}".strip()


def main():
    print("=" * 82)
    print("TFT INSIGHT - RANK OBSERVATION HISTORY V1 - REAL")
    print("=" * 82)

    game_name = input("Riot ID (Game Name): ").strip()
    tag_line = input("Tag: ").strip()

    result = RankObservationService().observe(
        game_name=game_name,
        tag_line=tag_line,
    )

    obs = result["observation"]
    previous = result["previous_observation"]

    print("\n" + "=" * 82)
    print("OBSERVAÇÃO DE ELO")
    print("=" * 82)
    print(f"Jogador                    : {game_name}#{tag_line}")
    print(f"Elo observado agora        : {rank_text(obs)}")
    print(f"Fila                       : {obs['queue_type']}")
    print(f"Última partida observada   : {obs['latest_match_id'] or '-'}")
    print(f"Observação anterior        : {rank_text(previous) if previous else '-'}")
    print(f"Partida anterior de corte  : {obs['previous_latest_match_id'] or '-'}")
    print(
        "Partidas desde consulta ant.: "
        f"{obs['matches_since_previous_rank_snapshot']}"
    )
    print(f"Associação                 : {obs['association']}")
    print(f"Total de snapshots de elo  : {result['total_observations']}")

    if obs["new_match_ids"]:
        print("\nPARTIDAS DO INTERVALO")
        for index, match_id in enumerate(reversed(obs["new_match_ids"]), 1):
            print(f"{index}. {match_id}")
    else:
        print("\nPARTIDAS DO INTERVALO")
        print("Nenhuma nova partida associada.")

    print("\nLEITURA")
    association = obs["association"]
    if association == "BASELINE":
        print(
            "Esta é a primeira observação. O elo atual cria o ponto de corte "
            "para medir quantas partidas ocorrerão até a próxima consulta."
        )
    elif association == "EXACT":
        print(
            "Uma única partida nova foi encontrada desde o snapshot anterior. "
            "O elo atual foi observado após essa única nova partida."
        )
    elif association == "INTERVAL":
        print(
            "Mais de uma partida ocorreu entre os snapshots. O elo atual "
            "pertence ao fim dessa janela; não atribuímos elo exato a cada partida."
        )
    elif association == "TRUNCATED":
        print(
            "O snapshot anterior não apareceu na janela consultada. Existem "
            "pelo menos as partidas listadas, mas a contagem exata não é garantida."
        )
    else:
        print("Nenhuma nova partida ocorreu desde a observação anterior.")

    print("\nPERSISTÊNCIA")
    print(result["history_path"])

    print("\n" + "=" * 82)
    print("IMPORTANTE")
    print("=" * 82)
    print("RANKED_TFT_DOUBLE_UP não é usado para o benchmark principal.")
    print("O sistema registra elo OBSERVADO, não inventa rank_at_match.")
    print("BASELINE não associa retroativamente partidas antigas ao elo atual.")
    print("EXACT significa 1 nova partida entre duas observações.")
    print("INTERVAL significa 2+ partidas entre duas observações.")
    print("TRUNCATED significa que a janela consultada não alcançou o corte anterior.")

    print("\n" + "=" * 82)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("Envie desde 'OBSERVAÇÃO DE ELO' até o final.")
    print("=" * 82)


if __name__ == "__main__":
    main()
