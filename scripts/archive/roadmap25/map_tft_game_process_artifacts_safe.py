from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOTS = (
    Path(r"C:\Riot Games\League of Legends (PBE)\Logs"),
    Path(r"C:\Riot Games\League of Legends (PBE)\Config"),
    Path(r"C:\Riot Games\League of Legends (PBE)\Saved"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Riot Games",
)

TEXT_SUFFIXES = {
    ".log", ".txt", ".json", ".yaml", ".yml", ".cfg", ".ini", ".xml",
}

MAX_FILE_SIZE = 50 * 1024 * 1024
TAIL_BYTES = 16384

TERMS = (
    "gold",
    "currentgold",
    "xp",
    "experience",
    "round",
    "stage",
    "level",
    "shop",
    "bench",
    "unit",
    "board",
    "health",
    "player",
    "gameplay",
    "teamfighttactics",
    "tft",
)

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "Crashpad",
    "Crashes",
    "GPUCache",
    "Code Cache",
    "Cache",
    "DawnCache",
}

TOKEN_PATTERNS = (
    re.compile(r'(?i)(authorization|auth[-_ ]?token|access[-_ ]?token|session[-_ ]?token|entitlements[-_ ]?token)\s*[:=]\s*["\']?[^"\',\s]+'),
    re.compile(r'(?i)(--(?:riotclient-auth-token|remoting-auth-token))=([^\s"]+)'),
    re.compile(r'(?i)(Bearer)\s+[A-Za-z0-9._~+/=-]+'),
    re.compile(r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
)


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def redact_text(text: str) -> str:
    redacted = text

    for pattern in TOKEN_PATTERNS:
        if pattern.pattern.startswith("(?i)("):
            redacted = pattern.sub(lambda m: f"{m.group(1)}=<REDACTED>", redacted)
        elif pattern.pattern.startswith("eyJ"):
            redacted = pattern.sub("<JWT_REDACTED>", redacted)
        else:
            redacted = pattern.sub("<REDACTED>", redacted)

    redacted = re.sub(
        r'https://riot:[^@\s]+@127\.0\.0\.1',
        'https://riot:<REDACTED>@127.0.0.1',
        redacted,
        flags=re.IGNORECASE,
    )
    return redacted


def interesting_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        low = line.lower()
        if any(term in low for term in TERMS):
            lines.append(line)
    return lines[:200]


def should_skip_dir(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def file_meta(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        st = path.stat()
    except OSError:
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

        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)

            dirnames[:] = [
                name for name in dirnames
                if name not in EXCLUDED_DIRS
            ]

            if should_skip_dir(current):
                continue

            for filename in filenames:
                path = current / filename
                meta = file_meta(path)

                if not meta:
                    continue

                if meta["suffix"] and meta["suffix"] not in TEXT_SUFFIXES:
                    continue

                if meta["size"] > MAX_FILE_SIZE:
                    continue

                data[str(path)] = meta

    return data


def diff(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    created = []
    modified = []

    before_keys = set(before)
    after_keys = set(after)

    for path in sorted(after_keys - before_keys):
        created.append(after[path])

    for path in sorted(before_keys & after_keys):
        b = before[path]
        a = after[path]
        if b["mtime_ns"] != a["mtime_ns"] or b["size"] != a["size"]:
            modified.append({
                "path": path,
                "before_size": b["size"],
                "after_size": a["size"],
                "suffix": a["suffix"],
            })

    return {
        "created": created,
        "modified": modified,
    }


def tail(path: Path) -> str:
    try:
        size = path.stat().st_size
        if size <= 0 or size > MAX_FILE_SIZE:
            return ""

        with path.open("rb") as f:
            if size > TAIL_BYTES:
                f.seek(size - TAIL_BYTES)
            raw = f.read(TAIL_BYTES)

        return redact_text(raw.decode("utf-8", errors="replace"))
    except OSError:
        return ""


def find_game_pid_from_settings() -> int | None:
    candidates = (
        Path(r"C:\Riot Games\League of Legends (PBE)\Config\LeagueClientSettings.yaml"),
        Path(r"C:\Riot Games\League of Legends\Config\LeagueClientSettings.yaml"),
    )

    pattern = re.compile(r'gameflow-process-info:\s*(?:\r?\n)+\s*pid:\s*(\d+)', re.IGNORECASE)

    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        match = pattern.search(text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Mapeia artefatos/logs alterados durante a partida TFT e "
            "destaca somente linhas relevantes, com redaction automatica."
        )
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=30,
        help="Segundos entre os dois snapshots.",
    )
    parser.add_argument(
        "--output",
        default="data/game_process_artifact_mapper",
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
    game_pid = find_game_pid_from_settings()

    print("=" * 112)
    print("TFT INSIGHT / ROADMAP 25.0M2 - GAME PROCESS ARTIFACT MAPPER")
    print("=" * 112)
    print(f"Game PID     : {game_pid if game_pid is not None else 'NAO IDENTIFICADO'}")
    print(f"Janela       : {args.wait}s")
    print("Rede         : NAO")
    print("Memoria      : NAO")
    print("Injecao      : NAO")
    print("Sniffing     : NAO")
    print("Input        : NAO")
    print("Redaction    : SIM")
    print()

    before = snapshot(roots)
    print(f"Snapshot A: {len(before)} arquivos")
    print(f"Aguardando {args.wait}s. Jogue normalmente...")
    time.sleep(args.wait)

    after = snapshot(roots)
    print(f"Snapshot B: {len(after)} arquivos")

    changes = diff(before, after)

    touched = []
    for kind in ("created", "modified"):
        for item in changes[kind]:
            path = Path(item["path"])
            text = tail(path)
            lines = interesting_lines(text)
            touched.append({
                "kind": kind,
                "path": str(path),
                "suffix": path.suffix.lower(),
                "interesting_lines": lines,
            })

    prioritized = [
        item for item in touched
        if item["interesting_lines"]
        or "game" in item["path"].lower()
        or "tft" in item["path"].lower()
        or "leagueclient" in item["path"].lower()
    ]

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    ts = stamp()

    payload = {
        "captured_at": ts,
        "game_pid": game_pid,
        "wait_seconds": args.wait,
        "policy": {
            "filesystem_only": True,
            "network_access": False,
            "memory_reading": False,
            "process_injection": False,
            "packet_sniffing": False,
            "input_automation": False,
            "redaction_enabled": True,
        },
        "roots": [str(x) for x in roots],
        "summary": {
            "created": len(changes["created"]),
            "modified": len(changes["modified"]),
            "prioritized": len(prioritized),
        },
        "prioritized": prioritized,
        "all_touched": touched,
    }

    jp = outdir / f"game_process_artifacts_{ts}.json"
    tp = outdir / f"game_process_artifacts_{ts}.txt"

    jp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "TFT INSIGHT / ROADMAP 25.0M2 - GAME PROCESS ARTIFACT MAPPER",
        "=" * 112,
        f"game_pid={game_pid}",
        f"wait_seconds={args.wait}",
        f"created={len(changes['created'])}",
        f"modified={len(changes['modified'])}",
        f"prioritized={len(prioritized)}",
        "",
    ]

    for item in prioritized:
        lines.append(f"[{item['kind']}] {item['path']}")
        if item["interesting_lines"]:
            lines.append("INTERESTING LINES:")
            lines.extend(item["interesting_lines"])
        else:
            lines.append("INTERESTING LINES: <none>")
        lines.append("-" * 112)

    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print(f"Criados     : {len(changes['created'])}")
    print(f"Modificados : {len(changes['modified'])}")
    print(f"Priorizados : {len(prioritized)}")
    print()
    print(f"JSON: {jp}")
    print(f"TXT : {tp}")
    print()
    print("Envie o TXT primeiro.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
