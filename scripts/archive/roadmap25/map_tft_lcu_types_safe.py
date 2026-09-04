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

COMMON_LOCKFILES = (
    Path(r"C:\Riot Games\League of Legends\lockfile"),
    Path(r"C:\Riot Games\League of Legends (PBE)\lockfile"),
    Path(r"C:\Riot Games\League of Legends PBE\lockfile"),
)

DEFAULT_TIMEOUT = 5.0

DEFAULT_TERMS = (
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
    "store",
    "roll",
    "reroll",
    "player",
    "gameflow",
    "gamestate",
    "game-state",
    "gameclient",
    "game-client",
    "tft",
)

SENSITIVE_TERMS = (
    "token",
    "password",
    "authorization",
    "secret",
    "credential",
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def find_lockfile(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(f"Lockfile nao encontrado: {p}")
        return p

    env = os.getenv("TFT_INSIGHT_LCU_LOCKFILE")
    if env:
        p = Path(env)
        if p.exists():
            return p

    for p in COMMON_LOCKFILES:
        if p.exists():
            return p

    raise FileNotFoundError(
        "Nenhum lockfile conhecido encontrado. Use --lockfile."
    )


def parse_lockfile(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="strict").strip()
    parts = raw.split(":")
    if len(parts) != 5:
        raise ValueError("Formato inesperado do lockfile.")

    name, pid, port, password, protocol = parts

    return {
        "name": name,
        "pid": int(pid),
        "port": int(port),
        "password": password,
        "protocol": protocol,
    }


def auth_header(password: str) -> str:
    token = base64.b64encode(
        f"riot:{password}".encode("utf-8")
    ).decode("ascii")
    return f"Basic {token}"


def safe_get_help(
    base_url: str,
    authorization: str,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url}/help"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": authorization,
                "Accept": "application/json",
            },
            timeout=timeout,
            verify=False,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result: dict[str, Any] = {
        "ok": response.ok,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
    }

    try:
        result["data"] = response.json()
    except ValueError:
        result["text_preview"] = response.text[:1000]

    return result


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def matches_terms(name: str, terms: tuple[str, ...]) -> bool:
    c = compact(name)
    return any(compact(term) in c for term in terms)


def sensitive(name: str) -> bool:
    lower = name.lower()
    return any(term in lower for term in SENSITIVE_TERMS)


def collect_types(help_data: Any) -> dict[str, Any]:
    if not isinstance(help_data, dict):
        return {}

    direct = help_data.get("types")
    if isinstance(direct, dict):
        return direct

    found: dict[str, Any] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            maybe = value.get("types")
            if isinstance(maybe, dict):
                found.update(maybe)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(help_data)
    return found


def flatten_type_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return repr(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Disseca somente a secao 'types' do GET /help do LCU. "
            "Filtra estruturas relacionadas a estado live/economia."
        )
    )
    parser.add_argument("--lockfile")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--output",
        default="data/lcu_type_mapper",
    )
    parser.add_argument(
        "--terms",
        nargs="*",
        default=list(DEFAULT_TERMS),
    )
    args = parser.parse_args()

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    terms = tuple(args.terms)

    lockfile = find_lockfile(args.lockfile)
    creds = parse_lockfile(lockfile)
    base_url = f"{creds['protocol']}://127.0.0.1:{creds['port']}"
    auth = auth_header(creds["password"])

    print("=" * 110)
    print("TFT INSIGHT / ROADMAP 25.0K - LCU TYPE MAPPER")
    print("=" * 110)
    print(f"Host      : {base_url}")
    print("Consulta  : GET /help")
    print("Secao     : types")
    print("Endpoints : nenhum outro endpoint chamado")
    print("Memoria   : NAO")
    print("Injecao   : NAO")
    print("Sniffing  : NAO")
    print("Input     : NAO")
    print()

    help_result = safe_get_help(
        base_url,
        auth,
        args.timeout,
    )

    if not help_result.get("ok"):
        raise SystemExit(
            f"/help falhou: {help_result.get('status_code', 'ERR')}"
        )

    help_data = help_result.get("data")
    types = collect_types(help_data)

    candidates = []

    for name, description in sorted(types.items()):
        if sensitive(name):
            continue

        text = flatten_type_value(description)

        relevance = matches_terms(name, terms) or matches_terms(text, terms)

        if relevance:
            candidates.append({
                "name": name,
                "description": text,
            })

    print(f"Types totais      : {len(types)}")
    print(f"Candidatos filtrados: {len(candidates)}")
    print()
    print("CANDIDATOS")
    print("-" * 110)

    for item in candidates[:250]:
        desc = item["description"].strip()
        if desc:
            print(f"- {item['name']} :: {desc}")
        else:
            print(f"- {item['name']}")

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    stamp = utc_stamp()

    json_path = outdir / f"type_map_{stamp}.json"
    txt_path = outdir / f"type_map_{stamp}.txt"

    payload = {
        "captured_at": stamp,
        "policy": {
            "localhost_only": True,
            "help_get_only": True,
            "other_endpoints_called": False,
            "memory_reading": False,
            "process_injection": False,
            "packet_sniffing": False,
            "input_automation": False,
            "credential_persistence": False,
        },
        "client": {
            "name": creds["name"],
            "pid": creds["pid"],
            "port": creds["port"],
            "protocol": creds["protocol"],
            "password": "<REDACTED>",
        },
        "terms": list(terms),
        "summary": {
            "types_total": len(types),
            "candidates_total": len(candidates),
        },
        "candidates": candidates,
    }

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "TFT INSIGHT / ROADMAP 25.0K - LCU TYPE MAPPER",
        "=" * 110,
        f"captured_at: {stamp}",
        "",
        f"types_total      : {len(types)}",
        f"candidates_total : {len(candidates)}",
        "",
        "CANDIDATOS",
        "-" * 110,
    ]

    for item in candidates:
        desc = item["description"].strip()
        if desc:
            lines.append(f"{item['name']} :: {desc}")
        else:
            lines.append(item["name"])

    txt_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"JSON salvo : {json_path}")
    print(f"TXT salvo  : {txt_path}")
    print()
    print(
        "Nenhum endpoint alem de /help foi chamado. "
        "Envie o TXT para revisao dos tipos."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
