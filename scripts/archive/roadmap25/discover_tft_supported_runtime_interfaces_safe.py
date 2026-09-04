from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOTS = (
    Path(r"C:\Riot Games\Teamfight Tactics\PBE"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Riot Games" / "Teamfight Tactics PBE",
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Riot Games" / "Metadata" / "teamfighttactics.pbe",
)

TEXT_SUFFIXES = {
    ".json", ".yaml", ".yml", ".ini", ".cfg", ".txt", ".log",
    ".xml", ".properties", ".manifest", ".toml", ".md",
}
MAX_FILE_SIZE = 8 * 1024 * 1024
MAX_HITS_PER_FILE = 80

# We are looking for static/documented/exposed interface clues only.
TERMS = (
    "endpoint", "localhost", "127.0.0.1", "api", "swagger", "openapi",
    "websocket", "wss://", "ws://", "http://", "https://",
    "telemetry", "schema", "plugin", "service", "rpc", "grpc",
    "gameflow", "teamfighttactics", "tft", "gold", "experience",
    "xp", "round", "stage", "shop", "bench", "board", "player",
)

SKIP_DIRS = {
    ".git", "__pycache__", "Cache", "Code Cache", "GPUCache",
    "DawnCache", "Crashpad", "Crashes",
}

SENSITIVE = (
    (re.compile(r'(?i)(authorization|auth[-_ ]?token|access[-_ ]?token|session[-_ ]?token|playerkey|spectatorkey|authorization-key)\s*[:=]\s*["\']?[^"\',\s]+'), r'\1=<REDACTED>'),
    (re.compile(r'eyJ[A-Za-z0-9_-]{20,}(?:\.[A-Za-z0-9_-]{20,}){0,2}'), "<TOKEN_REDACTED>"),
    (re.compile(r'(?i)(https?://[^:/\s]+:)[^@\s]+(@(?:127\.0\.0\.1|localhost))'), r'\1<REDACTED>\2'),
)

def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")

def redact(text):
    for pattern, repl in SENSITIVE:
        text = pattern.sub(repl, text)
    return text

def classify(line_lower):
    classes = []
    if any(x in line_lower for x in ("localhost", "127.0.0.1", "http://", "https://", "ws://", "wss://")):
        classes.append("network_reference")
    if any(x in line_lower for x in ("endpoint", "swagger", "openapi", "schema", "rpc", "grpc", "websocket")):
        classes.append("interface_reference")
    if any(x in line_lower for x in ("telemetry", "plugin", "service", "gameflow")):
        classes.append("runtime_reference")
    if any(x in line_lower for x in ("gold", "experience", " xp", "round", "stage", "shop", "bench", "board")):
        classes.append("gameplay_reference")
    return classes

def scan_file(path):
    try:
        st = path.stat()
        if st.st_size <= 0 or st.st_size > MAX_FILE_SIZE:
            return []
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    hits = []
    for number, raw in enumerate(text.splitlines(), 1):
        low = raw.lower()
        matched = sorted({term for term in TERMS if term in low})
        if not matched:
            continue
        safe = redact(raw.strip())
        hits.append({
            "line_number": number,
            "terms": matched,
            "classes": classify(low),
            "text": safe[:3000],
        })
        if len(hits) >= MAX_HITS_PER_FILE:
            break
    return hits

def main():
    ap = argparse.ArgumentParser(
        description="Offline/passive discovery of static TFT runtime interface clues."
    )
    ap.add_argument("--output", default="data/supported_runtime_interface_discovery")
    ap.add_argument("--roots", nargs="*", default=[str(x) for x in DEFAULT_ROOTS])
    args = ap.parse_args()

    roots = [Path(x) for x in args.roots]
    results = []
    scanned = 0

    print("=" * 112)
    print("TFT INSIGHT / ROADMAP 25.0O - SUPPORTED RUNTIME INTERFACE DISCOVERY")
    print("=" * 112)
    print("Modo          : OFFLINE / PASSIVO")
    print("Executaveis   : NAO inspecionados")
    print("Memoria       : NAO")
    print("Rede          : NAO")
    print("Endpoints     : NAO executados")
    print("Sniffing      : NAO")
    print("Injecao       : NAO")
    print()

    for root in roots:
        print("ROOT:", root)
        if not root.exists():
            continue

        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in fns:
                p = Path(dp) / fn
                if p.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                scanned += 1
                hits = scan_file(p)
                if hits:
                    results.append({
                        "path": str(p),
                        "hits": hits,
                    })

    # Prioritize files that combine interface/runtime clues with TFT/gameplay terms.
    for item in results:
        classes = {c for h in item["hits"] for c in h["classes"]}
        terms = {t for h in item["hits"] for t in h["terms"]}
        score = 0
        if "interface_reference" in classes: score += 4
        if "network_reference" in classes: score += 3
        if "runtime_reference" in classes: score += 2
        if "gameplay_reference" in classes: score += 3
        if "tft" in terms or "teamfighttactics" in terms: score += 2
        item["score"] = score

    results.sort(key=lambda x: (-x["score"], x["path"].lower()))

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    ts = stamp()
    jp = outdir / f"supported_interfaces_{ts}.json"
    tp = outdir / f"supported_interfaces_{ts}.txt"

    payload = {
        "captured_at": ts,
        "policy": {
            "offline_static_text_only": True,
            "binary_inspection": False,
            "memory_reading": False,
            "network_access": False,
            "endpoint_execution": False,
            "packet_sniffing": False,
            "process_injection": False,
            "input_automation": False,
            "redaction_enabled": True,
        },
        "roots": [str(x) for x in roots],
        "scanned_files": scanned,
        "matched_files": len(results),
        "results": results,
    }
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "TFT INSIGHT / ROADMAP 25.0O - SUPPORTED RUNTIME INTERFACE DISCOVERY",
        "=" * 112,
        f"scanned_files={scanned}",
        f"matched_files={len(results)}",
        "",
    ]
    for item in results[:100]:
        lines.append(f"SCORE={item['score']} FILE={item['path']}")
        for h in item["hits"]:
            lines.append(
                f"  L{h['line_number']} TERMS={','.join(h['terms'])} "
                f"CLASSES={','.join(h['classes']) or '-'}"
            )
            lines.append("  " + h["text"])
        lines.append("-" * 112)

    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print("Arquivos lidos :", scanned)
    print("Com pistas     :", len(results))
    print("JSON           :", jp)
    print("TXT            :", tp)
    print()
    print("Envie o TXT primeiro.")

if __name__ == "__main__":
    main()
