from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


from src.integration_engine.contracts import (
    CacheStatistics,
)
from src.integration_engine.services.cached_match_service import (
    CachedMatchService,
)
from src.integration_engine.services.internal_analysis_pipeline import (
    InternalAnalysisPipeline,
)


def main() -> None:
    game_name = input(
        "Nome do jogador: "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    count_text = input(
        "Quantidade de partidas [20]: "
    ).strip()

    match_count = (
        int(count_text)
        if count_text
        else 20
    )

    loader = CachedMatchService(
        project_root=PROJECT_ROOT
    )

    puuid = loader.resolve_puuid(
        puuid=None,
        game_name=game_name,
        tag_line=tag_line,
    )

    loaded = loader.load_player_matches(
        puuid=puuid,
        count=match_count,
    )

    pipeline = InternalAnalysisPipeline(
        project_root=PROJECT_ROOT
    )

    response = pipeline.analyze_matches(
        matches=loaded.matches,
        payloads=loaded.payloads,
        player_puuid=puuid,
        source="player",
        request_id=None,
        learn=True,
        cache_statistics=CacheStatistics(
            match_ids_received=(
                loaded.match_ids_received
            ),
            cached_matches_used=(
                loaded.cached_matches_used
            ),
            new_matches_downloaded=(
                loaded.new_matches_downloaded
            ),
            transformed_matches=len(
                loaded.matches
            ),
            failed_matches=(
                loaded.failed_matches
            ),
        ),
    )

    analysis = response.analysis

    print()
    print("=" * 100)
    print(
        "TFT INSIGHT - INTERNAL API INTEGRATION"
    )
    print("=" * 100)
    print(
        f"Partidas analisadas : "
        f"{response.matches_analyzed}"
    )
    print(
        f"Cache reutilizado   : "
        f"{response.cache.cached_matches_used}"
    )
    print(
        f"Novas baixadas      : "
        f"{response.cache.new_matches_downloaded}"
    )
    print(
        f"Learning inseridas  : "
        f"{response.learning.inserted}"
    )
    print(
        f"Learning reutilizadas: "
        f"{response.learning.reused}"
    )
    print(
        f"Score geral         : "
        f"{analysis.overall_score:.2f}"
    )
    print(
        f"Top 4               : "
        f"{analysis.prediction.top4_probability:.2f}%"
    )
    print(
        f"Confiança           : "
        f"{analysis.prediction.confidence:.2f}%"
    )
    print(
        f"Coach               : "
        f"{analysis.coach.headline}"
    )
    print(
        f"Ponto de atenção    : "
        f"{analysis.coach.pregame_attention}"
    )
    print()
    print(
        "✓ Riot → Cache → Transformers → Analyzers → "
        "Learning → Public Contract validados."
    )


if __name__ == "__main__":
    main()
