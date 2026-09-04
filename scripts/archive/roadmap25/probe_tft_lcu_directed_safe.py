from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
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

DEFAULT_TIMEOUT = 4.0

# Derivados diretamente do /help capturado.
# Whitelist pequena e fixa: somente GET.
WHITELIST_ENDPOINTS = {
    "gameflow_phase": "/lol-gameflow/v1/gameflow-phase",
    "gameflow_session": "/lol-gameflow/v1/session",
    "gameflow_player_status": (
        "/lol-gameflow/v1/gameflow-metadata/player-status"
    ),
    "gameflow_registration_status": (
        "/lol-gameflow/v1/gameflow-metadata/registration-status"
    ),
    "extra_game_client_args": (
        "/lol-gameflow/v1/extra-game-client-args"
    ),
    "lol_tft_root": "/lol-tft/v1/tft",
}


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
        raise ValueError(
            "Formato inesperado do lockfile. "
            "Esperado: name:pid:port:password:protocol"
        )

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


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            lower = key.lower()
            if (
                "token" in lower
                or "password" in lower
                or "authorization" in lower
                or "secret" in lower
            ):
                cleaned[key] = "<REDACTED>"
            else:
                cleaned[key] = redact(item)
        return cleaned

    if isinstance(value, list):
        return [redact(item) for item in value]

    return value


def safe_get(
    base_url: str,
    endpoint: str,
    authorization: str,
    timeout: float,
) -> dict[str, Any]:
    url = f"{base_url}{endpoint}"

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
            "endpoint": endpoint,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result: dict[str, Any] = {
        "ok": response.ok,
        "endpoint": endpoint,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
    }

    try:
        result["data"] = redact(response.json())
    except ValueError:
        result["text_preview"] = response.text[:1500]

    return result


def stable_digest(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def take_snapshot(
    base_url: str,
    authorization: str,
    timeout: float,
) -> dict[str, Any]:
    results: dict[str, Any] = {}

    for name, endpoint in WHITELIST_ENDPOINTS.items():
        results[name] = safe_get(
            base_url,
            endpoint,
            authorization,
            timeout,
        )

    return {
        "captured_at": utc_stamp(),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe direcionado de estado live do TFT via LCU. "
            "Somente GET, localhost, whitelist fixa."
        )
    )
    parser.add_argument("--lockfile")
    parser.add_argument(
        "--output",
        default="data/lcu_directed_probe",
    )
    parser.add_argument(
        "--label",
        default="in_game",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0,
        help=(
            "0 = uma captura. "
            ">0 = repete a cada N segundos ate Ctrl+C."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
    )
    args = parser.parse_args()

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    if args.interval < 0:
        raise SystemExit("--interval nao pode ser negativo.")

    if 0 < args.interval < 5:
        raise SystemExit(
            "Para manter o teste conservador, use --interval >= 5."
        )

    lockfile = find_lockfile(args.lockfile)
    creds = parse_lockfile(lockfile)
    base_url = f"{creds['protocol']}://127.0.0.1:{creds['port']}"
    auth = auth_header(creds["password"])

    print("=" * 112)
    print("TFT INSIGHT / ROADMAP 25.0H - DIRECTED LIVE STATE PROBE")
    print("=" * 112)
    print(f"Host      : {base_url}")
    print(f"Label     : {args.label}")
    print(f"Intervalo : {args.interval if args.interval else 'captura unica'}")
    print("Metodo    : GET somente")
    print("Whitelist : 6 endpoints")
    print("Memoria   : NAO")
    print("Injecao   : NAO")
    print("Input     : NAO")
    print()

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    last_digest: dict[str, str] = {}
    index = 0

    try:
        while True:
            index += 1
            snap = take_snapshot(
                base_url,
                auth,
                args.timeout,
            )

            changes: dict[str, bool] = {}

            print(
                f"[{index:03d}] {snap['captured_at']}"
            )

            for name, item in snap["results"].items():
                status = item.get("status_code", "ERR")
                digest = stable_digest(item.get("data"))
                changed = (
                    name not in last_digest
                    or digest != last_digest[name]
                )
                changes[name] = changed
                last_digest[name] = digest

                flag = "*" if changed else " "
                print(
                    f"  {flag} {name:<30} status={status}"
                )

            payload = {
                "captured_at": snap["captured_at"],
                "label": args.label,
                "sequence": index,
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
                "changed_since_previous": changes,
                "results": snap["results"],
            }

            path = outdir / (
                f"directed_probe_{args.label}_"
                f"{index:04d}_{snap['captured_at']}.json"
            )

            path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            if args.interval <= 0:
                print()
                print(f"Resultado salvo: {path}")
                break

            print()
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print()
        print("Coleta encerrada por Ctrl+C.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
