from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.role_inference import (
    CommunityDragonClient,
    CommunityDragonItemParser,
    HybridItemClassifier,
    ItemCatalogClassifier,
    ItemCategory,
    ItemClassification,
    ItemLearningCycle,
    ItemObservation,
    ItemObservationCollector,
    ItemObservationRepository,
    MetadataItemClassifier,
    RichItemData,
    RichItemRepository,
    RoleSeedAssessment,
    StatisticalItemClassifier,
    UnitRoleSeed,
    UnitRoleSeedInference,
)


def main() -> None:
    print("✓ Todos os imports do role_inference funcionaram.")


if __name__ == "__main__":
    main()
