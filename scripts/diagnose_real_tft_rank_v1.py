import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")


API_KEY = os.getenv("RIOT_API_KEY")

GAME_NAME = "pinador doss"
TAG_LINE = "000"

REGIONAL_HOST = "americas.api.riotgames.com"
PLATFORM_HOST = "br1.api.riotgames.com"


def main():
    print("=" * 80)
    print("TFT INSIGHT - DIAGNÓSTICO DE ELO REAL RIOT")
    print("=" * 80)

    if not API_KEY:
        raise RuntimeError("RIOT_API_KEY não encontrada no .env")

    headers = {
        "X-Riot-Token": API_KEY,
    }

    # ---------------------------------------------------------
    # 1. Riot ID -> PUUID
    # ---------------------------------------------------------

    print("\n[1] Resolvendo Riot ID...")

    account_url = (
        f"https://{REGIONAL_HOST}"
        f"/riot/account/v1/accounts/by-riot-id/"
        f"{GAME_NAME}/{TAG_LINE}"
    )

    response = requests.get(
        account_url,
        headers=headers,
        timeout=20,
    )

    print("HTTP Account:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        raise RuntimeError("Não foi possível resolver o Riot ID.")

    account = response.json()

    puuid = account["puuid"]

    print("Game Name :", account.get("gameName"))
    print("Tag       :", account.get("tagLine"))
    print("PUUID     :", puuid)

    # ---------------------------------------------------------
    # 2. PUUID -> Ranked TFT
    # ---------------------------------------------------------

    print("\n[2] Consultando TFT League-V1...")

    league_url = (
        f"https://{PLATFORM_HOST}"
        f"/tft/league/v1/by-puuid/{puuid}"
    )

    response = requests.get(
        league_url,
        headers=headers,
        timeout=20,
    )

    print("HTTP League:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        raise RuntimeError(
            "Não foi possível consultar TFT League-V1."
        )

    entries = response.json()

    print("\nEntradas retornadas:", len(entries))

    if not entries:
        print("\nNenhuma entrada ranqueada retornada pela Riot.")
        print("O jogador pode realmente estar não ranqueado.")
        return

    # ---------------------------------------------------------
    # 3. Mostrar retorno completo de cada fila
    # ---------------------------------------------------------

    for index, entry in enumerate(entries, start=1):

        print("\n" + "=" * 80)
        print(f"ENTRADA {index}")
        print("=" * 80)

        print("Queue Type   :", entry.get("queueType"))
        print("Tier         :", entry.get("tier"))
        print("Rank         :", entry.get("rank"))
        print("LeaguePoints :", entry.get("leaguePoints"))
        print("Wins         :", entry.get("wins"))
        print("Losses       :", entry.get("losses"))
        print("Hot Streak   :", entry.get("hotStreak"))
        print("Fresh Blood  :", entry.get("freshBlood"))
        print("Inactive     :", entry.get("inactive"))

    # ---------------------------------------------------------
    # 4. Encontrar Ranked TFT principal
    # ---------------------------------------------------------

    ranked_tft = next(
        (
            entry
            for entry in entries
            if entry.get("queueType") == "RANKED_TFT"
        ),
        None,
    )

    print("\n" + "=" * 80)
    print("RESULTADO TFT INSIGHT")
    print("=" * 80)

    if ranked_tft is None:
        print("RANKED_TFT não encontrada.")
        print("Não devemos inferir elo pelas partidas.")
        return

    tier = ranked_tft.get("tier")
    rank = ranked_tft.get("rank")
    lp = ranked_tft.get("leaguePoints")

    print(f"ELO REAL: {tier} {rank} - {lp} LP")

    wins = ranked_tft.get("wins", 0)
    losses = ranked_tft.get("losses", 0)

    total = wins + losses

    if total:
        winrate = wins / total * 100

        print(f"Partidas ranqueadas: {total}")
        print(f"Vitórias: {wins}")
        print(f"Derrotas: {losses}")
        print(f"Winrate: {winrate:.2f}%")

    print("\nVALIDAÇÃO CONCLUÍDA")


if __name__ == "__main__":
    main()