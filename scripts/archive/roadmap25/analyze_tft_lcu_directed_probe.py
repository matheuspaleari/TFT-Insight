from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TARGET_TERMS = (
    "gold",
    "economy",
    "income",
    "xp",
    "experience",
    "level",
    "round",
    "stage",
    "health",
    "damage",
    "bench",
    "shop",
    "roll",
    "unit",
    "item",
    "trait",
    "board",
)


def walk(value: Any, path: str, out: list[tuple[str, Any]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            walk(child, f"{path}.{key}", out)
    elif isinstance(value, list):
        for child in value:
            walk(child, f"{path}[]", out)
    else:
        lower = path.lower()
        if any(term in lower for term in TARGET_TERMS):
            out.append((path, value))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resume uma pasta de directed_probe e mostra "
            "quais endpoints mudaram e quais campos de interesse apareceram."
        )
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default="data/lcu_directed_probe",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    files = sorted(folder.glob("directed_probe_*.json"))

    if not files:
        raise SystemExit(
            f"Nenhum directed_probe_*.json encontrado em {folder}"
        )

    endpoint_statuses: dict[str, set[Any]] = {}
    endpoint_changes: dict[str, int] = {}
    interesting_paths: dict[str, set[str]] = {}

    for file in files:
        root = json.loads(
            file.read_text(encoding="utf-8")
        )

        changed = root.get(
            "changed_since_previous",
            {},
        )

        for name, item in root.get("results", {}).items():
            endpoint_statuses.setdefault(name, set()).add(
                item.get("status_code", "ERR")
            )

            if changed.get(name):
                endpoint_changes[name] = (
                    endpoint_changes.get(name, 0) + 1
                )

            leaves: list[tuple[str, Any]] = []
            walk(
                item.get("data"),
                f"$.results.{name}.data",
                leaves,
            )

            for path, value in leaves:
                interesting_paths.setdefault(
                    name,
                    set(),
                ).add(
                    f"{path} = {value!r}"
                )

    print("=" * 112)
    print("TFT INSIGHT / ROADMAP 25.0H - DIRECTED PROBE ANALYSIS")
    print("=" * 112)
    print(f"Arquivos analisados: {len(files)}")
    print()

    for name in sorted(endpoint_statuses):
        statuses = ", ".join(
            str(x)
            for x in sorted(
                endpoint_statuses[name],
                key=str,
            )
        )
        changes = endpoint_changes.get(name, 0)

        print(
            f"{name:<32} "
            f"status=[{statuses}] "
            f"changes={changes}"
        )

        paths = sorted(
            interesting_paths.get(name, set())
        )

        for path in paths[:80]:
            print(f"    {path}")

        if len(paths) > 80:
            print(
                f"    ... +{len(paths) - 80} campos/valores"
            )

        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
