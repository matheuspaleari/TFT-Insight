from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.sprint1_engine import KnowledgeRepository


def main() -> None:
    repository = KnowledgeRepository()
    repository.initialize()
    print("=" * 80)
    print("TFT INSIGHT - SPRINT 1 KNOWLEDGE DATABASE")
    print("=" * 80)
    print(f"Banco: {repository.path}")
    print("✓ SQLite inicializado com WAL, índices e schema versionado.")


if __name__ == "__main__":
    main()
