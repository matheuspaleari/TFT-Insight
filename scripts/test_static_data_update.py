from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.static_data import (
    DataDragonClient,
    StaticDataRepository,
    StaticDataUpdateService,
)


def main() -> None:
    catalog = StaticDataUpdateService(
        client=DataDragonClient(),
        repository=StaticDataRepository(),
        locale="pt_BR",
    ).load_latest()

    print()
    print("=" * 80)
    print("TFT INSIGHT - STATIC DATA")
    print("=" * 80)
    print(f"Versão    : {catalog.version}")
    print(f"Localidade: {catalog.locale}")
    print(f"Campeões  : {len(catalog.units)}")
    print(f"Itens     : {len(catalog.items)}")
    print(f"Traits    : {len(catalog.traits)}")

    if not catalog.units or not catalog.items or not catalog.traits:
        raise AssertionError(
            "O catálogo estático ficou incompleto."
        )

    print()
    print("✓ Dados estáticos validados com sucesso.")


if __name__ == "__main__":
    main()
