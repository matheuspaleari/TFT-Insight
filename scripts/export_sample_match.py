from pathlib import Path
import json
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.riot_client import RiotClient


def main() -> None:
    riot_client = RiotClient()

    game_name = "Pinador Doss"
    tag_line = "000"

    account = riot_client.get_account(
        game_name=game_name,
        tag_line=tag_line,
    )

    puuid = account["puuid"]

    match_ids = riot_client.get_match_ids(
        puuid=puuid,
        count=1,
    )

    if not match_ids:
        raise RuntimeError(
            "Nenhuma partida encontrada."
        )

    match_id = match_ids[0]

    match_data = riot_client.get_match_details(
        match_id=match_id,
    )

    output_path = Path(
        "data/debug/sample_match.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            match_data,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    print(
        f"JSON salvo em: {output_path}"
    )


if __name__ == "__main__":
    main()