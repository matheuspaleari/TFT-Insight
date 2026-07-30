import sqlite3
from pathlib import Path


DATABASE_PATH = Path("database/tft_insight.db")


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Banco não encontrado: {DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM matches"
        )
        total_matches = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM players"
        )
        total_players = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM traits"
        )
        total_traits = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM units"
        )
        total_units = cursor.fetchone()[0]

    print("=" * 50)
    print("Validação do banco")
    print("=" * 50)
    print(f"Partidas: {total_matches}")
    print(f"Jogadores: {total_players}")
    print(f"Traits: {total_traits}")
    print(f"Unidades: {total_units}")


if __name__ == "__main__":
    main()