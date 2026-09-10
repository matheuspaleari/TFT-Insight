from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.partner_analytics import PartnerAnalyticsRepository


def main() -> None:
    repository = PartnerAnalyticsRepository()
    repository.initialize()

    print("=" * 84)
    print("TFT INSIGHT - PARTNER ANALYTICS")
    print("=" * 84)
    print("Banco: PostgreSQL via DATABASE_URL")
    print("✓ Partner Analytics schema 2.0.0 inicializado.")


if __name__ == "__main__":
    main()
