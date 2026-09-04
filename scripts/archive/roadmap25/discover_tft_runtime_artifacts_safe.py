from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOTS = (
    Path(r"C:\Riot Games\League of Legends (PBE)\Logs"),
    Path(r"C:\Riot Games\League of Legends (PBE)"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Riot Games",
    Path(r"C:\ProgramData\Riot Games"),
)

EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    "Crashpad",
    "Crashes",
    "GPUCache",
    "Code Cache",
    "Cache",
    "DawnCache",
}

INTERESTING_SUFFIXES = {
    ".log", ".txt", ".json", ".yaml", ".yml", ".cfg", ".ini", ".xml",
}

MAX_FILE_SIZE = 50 * 1024 * 1024


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def should_skip_dir(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def file_meta(path: Path) -> dict[str, Any] | None:
    try:
        st = path.stat()
    except OSError:
        return None

    if not path.is_file():
        return None

    return {
        "path": str(path),
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "suffix": path.suffix.lower(),
    }


def snapshot(roots: list[Path]) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}

    for root in roots:
        if not root.exists():
            continue

        if root.is_file():
            meta = file_meta(root)
            if meta:
                data[str(root)] = meta
            continue

        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)

            dirnames[:] = [
                name for name in dirnames
                if name not in EXCLUDED_DIR_NAMES
            ]

            if should_skip_dir(current):
                continue

            for filename in filenames:
                path = current / filename
                meta = file_meta(path)
                if not meta:
                    continue

                suffix = meta["suffix"]
                if suffix and suffix not in INTERESTING_SUFFIXES:
                    continue

                if meta["size"] > MAX_FILE_SIZE:
                    continue

                data[str(path)] = meta

    return data


def diff_snapshots(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    created = []
    modified = []
    deleted = []

    before_keys = set(before)
    after_keys = set(after)

    for path in sorted(after_keys - before_keys):
        created.append(after[path])

    for path in sorted(before_keys - after_keys):
        deleted.append(before[path])

    for path in sorted(before_keys & after_keys):
        b = before[path]
        a = after[path]
        if (
            b["mtime_ns"] != a["mtime_ns"]
            or b["size"] != a["size"]
        ):
            modified.append({
                "path": path,
                "before_size": b["size"],
                "after_size": a["size"],
                "before_mtime_ns": b["mtime_ns"],
                "after_mtime_ns": a["mtime_ns"],
                "suffix": a["suffix"],
            })

    return {
        "created": created,
        "modified": modified,
        "deleted": deleted,
    }


def safe_tail(path: Path, max_bytes: int = 8192) -> str | None:
    try:
        size = path.stat().st_size
        if size == 0 or size > MAX_FILE_SIZE:
            return None

        with path.open("rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
            raw = f.read(max_bytes)

        return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def summarize_diff(diff: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    touched = []

    for kind in ("created", "modified"):
        for item in diff[kind]:
            path = Path(item["path"])
            tail = None
            if path.suffix.lower() in INTERESTING_SUFFIXES:
                tail = safe_tail(path)

            touched.append({
                "kind": kind,
                "path": str(path),
                "suffix": path.suffix.lower(),
                "tail_preview": tail,
            })

    return {
        "touched_files": touched,
        "counts": {
            "created": len(diff["created"]),
            "modified": len(diff["modified"]),
            "deleted": len(diff["deleted"]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Descobre arquivos/logs modificados durante uma janela curta "
            "enquanto o TFT roda. Nao le memoria nem captura rede."
        )
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=30,
        help="Segundos entre snapshot A e B.",
    )
    parser.add_argument(
        "--output",
        default="data/runtime_artifact_discovery",
    )
    parser.add_argument(
        "--roots",
        nargs="*",
        default=[str(x) for x in DEFAULT_ROOTS],
    )
    args = parser.parse_args()

    if args.wait < 5 or args.wait > 180:
        raise SystemExit("Use --wait entre 5 e 180 segundos.")

    roots = [Path(x) for x in args.roots]

    print("=" * 112)
    print("TFT INSIGHT / ROADMAP 25.0M - RUNTIME ARTIFACT DISCOVERY")
    print("=" * 112)
    print(f"Janela       : {args.wait}s")
    print("Memoria      : NAO")
    print("Injecao      : NAO")
    print("Sniffing     : NAO")
    print("Input        : NAO")
    print("Rede         : NAO")
    print()
    print("Raizes:")
    for root in roots:
        print(f" - {root}")
    print()
    print("Snapshot A...")

    before = snapshot(roots)
    print(f"Arquivos observados: {len(before)}")
    print(f"Aguardando {args.wait}s. Jogue normalmente...")
    time.sleep(args.wait)

    print("Snapshot B...")
    after = snapshot(roots)
    print(f"Arquivos observados: {len(after)}")

    diff = diff_snapshots(before, after)
    summary = summarize_diff(diff)

    print()
    print("RESULTADO")
    print("-" * 112)
    print(f"Criados    : {summary['counts']['created']}")
    print(f"Modificados: {summary['counts']['modified']}")
    print(f"Deletados  : {summary['counts']['deleted']}")
    print()

    for item in summary["touched_files"][:80]:
        print(f"[{item['kind']}] {item['path']}")

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    ts = stamp()

    payload = {
        "captured_at": ts,
        "wait_seconds": args.wait,
        "policy": {
            "filesystem_metadata_only": True,
            "memory_reading": False,
            "process_injection": False,
            "packet_sniffing": False,
            "input_automation": False,
            "network_access": False,
        },
        "roots": [str(x) for x in roots],
        "diff": diff,
        "summary": summary,
    }

    jp = outdir / f"runtime_artifacts_{ts}.json"
    tp = outdir / f"runtime_artifacts_{ts}.txt"

    jp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "TFT INSIGHT / ROADMAP 25.0M - RUNTIME ARTIFACT DISCOVERY",
        "=" * 112,
        f"wait_seconds={args.wait}",
        f"created={summary['counts']['created']}",
        f"modified={summary['counts']['modified']}",
        f"deleted={summary['counts']['deleted']}",
        "",
    ]

    for item in summary["touched_files"]:
        lines.append(f"[{item['kind']}] {item['path']}")
        if item["tail_preview"]:
            lines.append("--- tail preview ---")
            lines.append(item["tail_preview"])
            lines.append("--- end tail ---")
        lines.append("-" * 112)

    tp.write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"JSON: {jp}")
    print(f"TXT : {tp}")
    print()
    print("Envie o TXT primeiro.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
