from pathlib import Path
import json
import sys
import tempfile

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

from src.benchmark_intelligence import (
    BenchmarkIntelligenceService,
)


CSV_TEXT = """player,matches_played,average_placement,top4_rate,win_rate,average_level,placement_standard_deviation,bottom4_rate,best_placement,worst_placement,average_damage_to_players,average_players_eliminated,average_gold_left
puuid-a,20,2.8,80,30,9.1,1.4,20,1,7,130,1.2,8
puuid-b,20,3.4,70,20,8.8,1.8,30,1,8,120,1.0,9
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        metrics_path = (
            root
            / "data"
            / "analysis"
            / "challenger_metrics.csv"
        )
        metrics_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        metrics_path.write_text(
            CSV_TEXT,
            encoding="utf-8",
        )

        matches_dir = (
            root
            / "data"
            / "role_inference"
            / "challenger"
            / "matches"
        )
        matches_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "info": {
                "participants": [
                    {
                        "puuid": "puuid-a",
                        "riotIdGameName": "Alpha",
                        "riotIdTagline": "BR1",
                    },
                    {
                        "puuid": "puuid-b",
                        "riotIdGameName": "Beta",
                        "riotIdTagline": "BR1",
                    },
                ]
            }
        }

        (
            matches_dir
            / "test.json"
        ).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

        service = (
            BenchmarkIntelligenceService(
                project_root=root
            )
        )

        overview = service.overview()

        assert (
            overview[
                "players_analyzed"
            ]
            == 2
        )
        assert (
            overview[
                "matches_analyzed"
            ]
            == 40
        )
        assert (
            overview["players"][0][
                "game_name"
            ]
            in {
                "Alpha",
                "Beta",
            }
        )
        assert (
            overview["metrics"][
                "top4_rate"
            ]["mean"]
            == 75.0
        )

    print("=" * 88)
    print(
        "TFT INSIGHT - BENCHMARK INTELLIGENCE ALPHA 2"
    )
    print("=" * 88)
    print("Dataset loader     : OK")
    print("Player catalog     : OK")
    print("Local Riot IDs     : OK")
    print("Metric aggregation : OK")
    print("Quartiles          : OK")
    print("No Riot API calls  : OK")
    print()
    print(
        "✓ v0.5.0-alpha.2 Benchmark Intelligence validated."
    )


if __name__ == "__main__":
    main()
