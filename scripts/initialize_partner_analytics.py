from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.partner_analytics import PartnerAnalyticsRepository


def main() -> None:
    repository = PartnerAnalyticsRepository(
        PROJECT_ROOT
        / "data"
        / "partner"
        / "partner_analytics.db"
    )
    repository.initialize()

    print("=" * 84)
    print("TFT INSIGHT - PARTNER ANALYTICS")
    print("=" * 84)
    print(
        "Banco: data/partner/partner_analytics.db"
    )
    print(
        "✓ Partner Analytics schema 1.1.0 inicializado."
    )


if __name__ == "__main__":
    main()
