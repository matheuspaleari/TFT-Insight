from __future__ import annotations

import argparse
import base64
import json
import os
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

# Lista pequena e deliberada de endpoints GET conhecidos/documentados
# em clientes LCU antigos/atuais ou úteis ao ciclo de vida da partida.
LCU_CANDIDATES = (
    "/help",
    "/lol-gameflow/v1/availability",
    "/lol-gameflow/v1/game-client",
    "/lol-gameflow/v1/gameflow-phase",
    "/lol-gameflow/v1/gameflow-metadata/player-status",
    "/lol-gameflow/v1/session",
    "/lol-gameflow/v1/watch",
    "/lol-summoner/v1/current-summoner",
    "/lol-login/v1/session",
    "/riotclient/region-locale",
)

DEFAULT_TIMEOUT = 3.0


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
    token = base64.b64encode(f"riot:{password}".encode()).decode()
    return f"Basic {token}"


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            lower = key.lower()
            if "token" in lower or "password" in lower or "authorization" in lower:
                out[key] = "<REDACTED>"
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(x) for x in value]
    return value


def safe_get(
    base_url: str,
    endpoint: str,
    authorization: str,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url}{endpoint}"
    try:
        r = requests.get(
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
            "endpoint": endpoint,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result: dict[str, Any] = {
        "endpoint": endpoint,
        "ok": r.ok,
        "status_code": r.status_code,
        "content_type": r.headers.get("content-type", ""),
    }

    try:
        result["data"] = redact(r.json())
    except ValueError:
        result["text_preview"] = r.text[:1500]

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Descoberta conservadora de endpoints LCU para TFT Insight. "
            "Somente GET, localhost, whitelist pequena."
        )
    )
    parser.add_argument("--lockfile")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--output",
        default="data/lcu_endpoint_probe",
    )
    args = parser.parse_args()

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    lockfile = find_lockfile(args.lockfile)
    creds = parse_lockfile(lockfile)
    base_url = f"{creds['protocol']}://127.0.0.1:{creds['port']}"
    auth = auth_header(creds["password"])

    print("=" * 100)
    print("TFT INSIGHT / ROADMAP 25.0C - SAFE ENDPOINT DISCOVERY")
    print("=" * 100)
    print(f"Host    : {base_url}")
    print("Metodo  : GET somente")
    print("Escopo  : whitelist pequena")
    print("Memoria : NAO")
    print("Injecao : NAO")
    print("Input   : NAO")
    print()

    results = []

    for endpoint in LCU_CANDIDATES:
        item = safe_get(base_url, endpoint, auth, args.timeout)
        results.append(item)

        status = item.get("status_code", "ERR")
        print(f"{endpoint:<55} {status}")

    payload = {
        "captured_at": utc_stamp(),
        "policy": {
            "localhost_only": True,
            "get_only": True,
            "whitelist_only": True,
            "memory_reading": False,
            "process_injection": False,
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
        "results": results,
    }

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"endpoint_probe_{utc_stamp()}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Resultado salvo: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
