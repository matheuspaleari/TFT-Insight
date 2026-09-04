from __future__ import annotations
import argparse, base64, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOCKFILES = (
    Path(r"C:\Riot Games\League of Legends (PBE)\lockfile"),
    Path(r"C:\Riot Games\League of Legends\lockfile"),
    Path(r"C:\Riot Games\League of Legends PBE\lockfile"),
)

TARGET_TYPES = (
    "LolTftGameflowGameData",
    "LolTftGameflowPhase",
    "LolTftGameflowSession",
    "LolGameflowGameStateUpdate",
    "LolGameflowGameflowGameClient",
    "LolGameflowGameflowGameData",
    "LolGameflowGameflowPhase",
    "LolGameflowGameflowSession",
    "LolEndOfGameGameStateUpdate",
    "LolTftEventGameflowGameData",
    "LolTftEventGameflowPhase",
    "LolTftEventGameflowSession",
    "BindingFullApiHelp",
)

TERMS = (
    "currentGold", "gold", "economy", "income", "xp", "experience",
    "round", "stage", "level", "playerState", "gameState", "tft",
)

SENSITIVE = ("password", "token", "authorization", "secret", "credential")


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def lockfile(explicit):
    if explicit:
        p = Path(explicit)
        if p.exists(): return p
        raise FileNotFoundError(p)
    env = os.getenv("TFT_INSIGHT_LCU_LOCKFILE")
    if env and Path(env).exists(): return Path(env)
    for p in LOCKFILES:
        if p.exists(): return p
    raise FileNotFoundError("Lockfile LCU nao encontrado. Use --lockfile.")


def creds(path):
    parts = path.read_text(encoding="utf-8").strip().split(":")
    if len(parts) != 5: raise ValueError("Lockfile inesperado.")
    name, pid, port, password, protocol = parts
    return name, int(pid), int(port), password, protocol


def auth(password):
    token = base64.b64encode(f"riot:{password}".encode()).decode()
    return f"Basic {token}"


def redact(obj: Any):
    if isinstance(obj, dict):
        return {
            k: ("<REDACTED>" if any(x in k.lower() for x in SENSITIVE) else redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list): return [redact(v) for v in obj]
    return obj


def scalar_text(obj: Any) -> str:
    try: return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except TypeError: return repr(obj)


def walk(obj: Any, path="$"):
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def classify(path: str, obj: Any) -> str:
    s = (path + " " + scalar_text(obj)[:500]).lower()
    if "event" in s: return "event"
    if "function" in s or "method" in s: return "function"
    if "type" in s: return "type"
    return "reference"


def context_hits(data: Any):
    hits = []
    seen = set()
    needles = TARGET_TYPES + TERMS
    for path, obj in walk(data):
        text = scalar_text(obj)
        matched = [n for n in needles if n.lower() in text.lower() or n.lower() in path.lower()]
        if not matched: continue

        # Keep useful structural nodes, not every scalar child.
        if not isinstance(obj, (dict, list)): continue
        key = (path, tuple(sorted(set(matched))))
        if key in seen: continue
        seen.add(key)

        preview = redact(obj)
        serialized = scalar_text(preview)
        if len(serialized) > 12000:
            serialized = serialized[:12000] + "...<TRUNCATED>"

        uris = sorted(set(re.findall(r'/(?:lol|riot|plugin|data|help)[A-Za-z0-9_./{}:-]*', serialized)))
        hits.append({
            "path": path,
            "kind": classify(path, obj),
            "matched": sorted(set(matched), key=str.lower),
            "uris": uris[:50],
            "preview": serialized,
        })
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lockfile")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--output", default="data/lcu_type_cross_mapper")
    args = ap.parse_args()

    lp = lockfile(args.lockfile)
    name, pid, port, password, protocol = creds(lp)
    base = f"{protocol}://127.0.0.1:{port}"

    print("="*108)
    print("TFT INSIGHT / ROADMAP 25.0L - TYPE -> FUNCTION/EVENT CROSS MAPPER")
    print("="*108)
    print("Consulta : GET /help somente")
    print("Execucao de endpoints encontrados: NAO")
    print("Memoria/injecao/sniffing/input     : NAO")
    print()

    r = requests.get(
        base + "/help",
        headers={"Authorization": auth(password), "Accept": "application/json"},
        verify=False, timeout=args.timeout, allow_redirects=False,
    )
    r.raise_for_status()
    data = r.json()

    hits = context_hits(data)

    # Prefer nodes that expose a URI or directly match a target type.
    useful = [
        h for h in hits
        if h["uris"] or any(t in h["matched"] for t in TARGET_TYPES)
    ]

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    ts = stamp()

    payload = {
        "captured_at": ts,
        "policy": {
            "localhost_only": True,
            "help_get_only": True,
            "discovered_endpoints_executed": False,
            "memory_reading": False,
            "process_injection": False,
            "packet_sniffing": False,
            "input_automation": False,
            "credential_persistence": False,
        },
        "client": {"name": name, "pid": pid, "port": port, "protocol": protocol, "password": "<REDACTED>"},
        "target_types": list(TARGET_TYPES),
        "terms": list(TERMS),
        "summary": {"all_hits": len(hits), "useful_hits": len(useful)},
        "hits": useful,
    }

    jp = outdir / f"type_cross_map_{ts}.json"
    tp = outdir / f"type_cross_map_{ts}.txt"
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "TFT INSIGHT / ROADMAP 25.0L - TYPE -> FUNCTION/EVENT CROSS MAPPER",
        "="*108,
        f"all_hits={len(hits)} useful_hits={len(useful)}",
        "",
    ]
    for i, h in enumerate(useful, 1):
        lines += [
            f"[{i}] kind={h['kind']}",
            f"path={h['path']}",
            "matched=" + ", ".join(h["matched"]),
            "uris=" + (", ".join(h["uris"]) if h["uris"] else "<none>"),
            "preview=" + h["preview"],
            "-"*108,
        ]
    tp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Hits estruturais : {len(hits)}")
    print(f"Hits uteis       : {len(useful)}")
    print(f"JSON             : {jp}")
    print(f"TXT              : {tp}")
    print()
    print("Envie o TXT. Nenhum endpoint descoberto foi executado.")


if __name__ == "__main__":
    main()
