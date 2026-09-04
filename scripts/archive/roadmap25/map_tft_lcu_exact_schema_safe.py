from __future__ import annotations

import argparse
import base64
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import urllib3

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
)

FIELD_TERMS = (
    "currentGold", "gold", "economy", "income", "xp", "experience",
    "round", "stage", "level", "playerState", "gameState",
    "health", "bench", "shop", "roll", "reroll",
)

SENSITIVE = ("password", "token", "authorization", "secret", "credential")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def get_lockfile(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(p)
        return p
    env = os.getenv("TFT_INSIGHT_LCU_LOCKFILE")
    if env and Path(env).exists():
        return Path(env)
    for p in LOCKFILES:
        if p.exists():
            return p
    raise FileNotFoundError("Lockfile LCU nao encontrado. Use --lockfile.")


def read_creds(path: Path):
    parts = path.read_text(encoding="utf-8").strip().split(":")
    if len(parts) != 5:
        raise ValueError("Formato inesperado do lockfile.")
    name, pid, port, password, protocol = parts
    return name, int(pid), int(port), password, protocol


def auth(password: str) -> str:
    token = base64.b64encode(f"riot:{password}".encode()).decode()
    return f"Basic {token}"


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: ("<REDACTED>" if any(s in k.lower() for s in SENSITIVE) else redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return repr(value)


def exact_type_mentions(obj: Any, target: str) -> list[str]:
    hits = []

    def walk(v: Any, path="$"):
        if isinstance(v, dict):
            for k, child in v.items():
                walk(child, f"{path}.{k}")
        elif isinstance(v, list):
            for i, child in enumerate(v):
                walk(child, f"{path}[{i}]")
        elif isinstance(v, str) and v == target:
            hits.append(path)

    walk(obj)
    return hits


def direct_term_hits(obj: Any) -> list[str]:
    found = set()

    def walk(v: Any):
        if isinstance(v, dict):
            for k, child in v.items():
                kl = k.lower()
                for term in FIELD_TERMS:
                    if term.lower() in kl:
                        found.add(k)
                walk(child)
        elif isinstance(v, list):
            for child in v:
                walk(child)

    walk(obj)
    return sorted(found, key=str.lower)


def section(help_data: dict[str, Any], name: str) -> Any:
    value = help_data.get(name)
    return value if value is not None else {}


def records(value: Any):
    if isinstance(value, dict):
        for name, body in value.items():
            yield str(name), body
    elif isinstance(value, list):
        for i, body in enumerate(value):
            if isinstance(body, dict):
                name = (
                    body.get("name")
                    or body.get("functionName")
                    or body.get("eventName")
                    or body.get("typeName")
                    or f"index_{i}"
                )
            else:
                name = f"index_{i}"
            yield str(name), body


def related_records(section_value: Any, target: str):
    result = []
    for name, body in records(section_value):
        paths = exact_type_mentions(body, target)
        if paths:
            result.append({
                "name": name,
                "mention_paths": paths,
                "body": redact(body),
            })
    return result


def uri_candidates(obj: Any) -> list[str]:
    text = norm(obj)
    return sorted(set(re.findall(
        r'/(?:lol|riot|plugin|data|help)[A-Za-z0-9_./{}:-]*',
        text,
    )))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lockfile")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--output", default="data/lcu_exact_schema_mapper")
    args = ap.parse_args()

    lf = get_lockfile(args.lockfile)
    name, pid, port, password, protocol = read_creds(lf)
    base = f"{protocol}://127.0.0.1:{port}"

    print("=" * 110)
    print("TFT INSIGHT / ROADMAP 25.0L2 - EXACT API SCHEMA MAPPER")
    print("=" * 110)
    print("Consulta                         : GET /help somente")
    print("Matching                         : referencias exatas de tipo")
    print("Endpoints descobertos executados : NAO")
    print("Memoria/injecao/sniffing/input   : NAO")
    print()

    r = requests.get(
        base + "/help",
        headers={"Authorization": auth(password), "Accept": "application/json"},
        verify=False,
        timeout=args.timeout,
        allow_redirects=False,
    )
    r.raise_for_status()
    help_data = r.json()

    if not isinstance(help_data, dict):
        raise SystemExit("/help nao retornou objeto JSON.")

    functions = section(help_data, "functions")
    events = section(help_data, "events")
    types = section(help_data, "types")

    report = []

    for target in TARGET_TYPES:
        type_body = None
        if isinstance(types, dict):
            type_body = types.get(target)

        fn_refs = related_records(functions, target)
        ev_refs = related_records(events, target)

        # Also detect direct references from other type definitions.
        type_refs = []
        for other_name, other_body in records(types):
            if other_name == target:
                continue
            paths = exact_type_mentions(other_body, target)
            if paths:
                type_refs.append({
                    "name": other_name,
                    "mention_paths": paths,
                })

        entry = {
            "target_type": target,
            "defined": type_body is not None,
            "definition": redact(type_body),
            "direct_field_term_hits": direct_term_hits(type_body),
            "function_refs": fn_refs,
            "event_refs": ev_refs,
            "type_refs": type_refs,
            "uri_candidates": sorted(set(
                uri
                for rec in (fn_refs + ev_refs)
                for uri in uri_candidates(rec["body"])
            )),
        }
        report.append(entry)

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    ts = stamp()

    payload = {
        "captured_at": ts,
        "policy": {
            "localhost_only": True,
            "help_get_only": True,
            "exact_type_matching": True,
            "discovered_endpoints_executed": False,
            "memory_reading": False,
            "process_injection": False,
            "packet_sniffing": False,
            "input_automation": False,
            "credential_persistence": False,
        },
        "client": {
            "name": name,
            "pid": pid,
            "port": port,
            "protocol": protocol,
            "password": "<REDACTED>",
        },
        "report": report,
    }

    jp = outdir / f"exact_schema_map_{ts}.json"
    tp = outdir / f"exact_schema_map_{ts}.txt"
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "TFT INSIGHT / ROADMAP 25.0L2 - EXACT API SCHEMA MAPPER",
        "=" * 110,
        "",
    ]

    promising = 0
    for e in report:
        score = (
            len(e["direct_field_term_hits"])
            + len(e["function_refs"])
            + len(e["event_refs"])
            + len(e["uri_candidates"])
        )
        if score:
            promising += 1

        lines += [
            f"TYPE: {e['target_type']}",
            f"defined: {e['defined']}",
            "field_hits: " + (", ".join(e["direct_field_term_hits"]) or "<none>"),
            "function_refs: " + str(len(e["function_refs"])),
            "event_refs: " + str(len(e["event_refs"])),
            "type_refs: " + str(len(e["type_refs"])),
            "uris: " + (", ".join(e["uri_candidates"]) or "<none>"),
        ]

        if e["definition"] is not None:
            lines.append("definition=" + norm(e["definition"])[:6000])

        for rec in e["function_refs"]:
            lines.append(
                "FUNCTION -> "
                + rec["name"]
                + " | paths="
                + ", ".join(rec["mention_paths"])
                + " | body="
                + norm(rec["body"])[:5000]
            )

        for rec in e["event_refs"]:
            lines.append(
                "EVENT -> "
                + rec["name"]
                + " | paths="
                + ", ".join(rec["mention_paths"])
                + " | body="
                + norm(rec["body"])[:5000]
            )

        for rec in e["type_refs"][:50]:
            lines.append(
                "TYPE_REF -> "
                + rec["name"]
                + " | paths="
                + ", ".join(rec["mention_paths"])
            )

        lines += ["-" * 110, ""]

    lines.insert(3, f"target_types={len(report)} promising={promising}")
    tp.write_text("\n".join(lines), encoding="utf-8")

    print(f"Tipos alvo       : {len(report)}")
    print(f"Com alguma pista : {promising}")
    print(f"JSON             : {jp}")
    print(f"TXT              : {tp}")
    print()
    print("Envie o TXT. Nenhum endpoint descoberto foi executado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
