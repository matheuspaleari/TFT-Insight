from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SDK_SRC = PROJECT_ROOT / "sdk" / "python" / "src"

if str(SDK_SRC) not in sys.path:
    sys.path.insert(0, str(SDK_SRC))


from tft_insight import TFTInsightClient


def main() -> None:
    game_name = input(
        "Nome do jogador: "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    with TFTInsightClient(
        base_url="http://127.0.0.1:8000",
        api_key=None,
        timeout=60.0,
    ) as client:
        health = client.health()

        report = client.analyze_player(
            game_name=game_name,
            tag_line=tag_line,
            match_count=20,
            learn=True,
        )

    print()
    print("=" * 90)
    print("TFT INSIGHT - SDK PYTHON")
    print("=" * 90)
    print(
        f"API                : {health.status}"
    )
    print(
        f"Partidas analisadas: "
        f"{report.matches_analyzed}"
    )
    print(
        f"Cache reutilizado  : "
        f"{report.cache.cached_matches_used}"
    )
    print(
        f"Score geral        : "
        f"{report.analysis.overall_score:.2f}"
    )
    print(
        f"Top 4              : "
        f"{report.analysis.prediction.top4_probability:.2f}%"
    )
    print(
        f"Confiança          : "
        f"{report.analysis.prediction.confidence:.2f}%"
    )
    print(
        f"Coach              : "
        f"{report.analysis.coach.headline}"
    )
    print()
    print("✓ SDK → API → Engine validado.")


if __name__ == "__main__":
    main()
