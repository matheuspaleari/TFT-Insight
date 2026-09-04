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

DEFAULT_TIMEOUT = 3.0

COMMON_LOCKFILES = (
    Path(r"C:\Riot Games\League of Legends\lockfile"),
    Path(r"C:\Riot Games\League of Legends (PBE)\lockfile"),
    Path(r"C:\Riot Games\League of Legends PBE\lockfile"),
)

SAFE_GET_ENDPOINTS = (
    "/lol-gameflow/v1/gameflow-phase",
    "/lol-gameflow/v1/session",
    "/lol-summoner/v1/current-summoner",
    "/lol-login/v1/session",
    "/riotclient/region-locale",
)

DISCOVERY_ENDPOINTS = (
    "/swagger/v1/openapi.json",
    "/swagger/v2/openapi.json",
    "/swagger/v3/openapi.json",
    "/swagger/v1/swagger.json",
    "/swagger/v2/swagger.json",
    "/swagger/v3/swagger.json",
)

KEYWORDS = (
    "tft",
    "gameflow",
    "match",
    "session",
    "spectator",
    "summoner",
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def parse_lockfile(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="strict").strip()
    parts = raw.split(":")

    if len(parts) != 5:
        raise ValueError(
            f"Formato inesperado de lockfile em {path}. "
            "Esperado: name:pid:port:password:protocol"
        )

    name, pid, port, password, protocol = parts

    return {
        "name": name,
        "pid": int(pid),
        "port": int(port),
        "password": password,
        "protocol": protocol,
        "path": str(path),
    }


def find_lockfile(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"Lockfile não encontrado: {path}")
        return path

    env_path = os.getenv("TFT_INSIGHT_LCU_LOCKFILE")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    for path in COMMON_LOCKFILES:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Nenhum lockfile conhecido foi encontrado. "
        "Use --lockfile \"C:\\caminho\\para\\lockfile\"."
    )


def auth_header(password: str) -> str:
    token = base64.b64encode(f"riot:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


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

    item: dict[str, Any] = {
        "ok": response.ok,
        "endpoint": endpoint,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
    }

    try:
        item["data"] = response.json()
    except ValueError:
        item["text_preview"] = response.text[:1000]

    return item


def extract_paths(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []

    paths = payload.get("paths")
    if not isinstance(paths, dict):
        return []

    return sorted(str(path) for path in paths)


def filter_interesting(paths: list[str]) -> list[str]:
    return [
        path
        for path in paths
        if any(keyword in path.lower() for keyword in KEYWORDS)
    ]


def redact_session_payload(value: Any) -> Any:
    """
    Remove campos que possam carregar tokens/credenciais.
    Não altera dados funcionais comuns de gameflow/sessão.
    """
    blocked = {
        "password",
        "token",
        "accessToken",
        "access_token",
        "idToken",
        "id_token",
        "authorization",
        "authToken",
        "auth_token",
        "entitlementsToken",
    }

    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in blocked or "token" in key.lower() or "password" in key.lower():
                result[key] = "<REDACTED>"
            else:
                result[key] = redact_session_payload(item)
        return result

    if isinstance(value, list):
        return [redact_session_payload(item) for item in value]

    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Descoberta segura do LCU para TFT Insight. "
            "Lê apenas o lockfile local e executa GETs HTTPS em localhost."
        )
    )
    parser.add_argument(
        "--lockfile",
        help="Caminho explícito para o lockfile do League Client/PBE.",
    )
    parser.add_argument(
        "--output",
        default="data/lcu_probe",
        help="Diretório de saída. Padrão: data/lcu_probe",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Timeout HTTP em segundos.",
    )

    args = parser.parse_args()

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    lockfile = find_lockfile(args.lockfile)
    credentials = parse_lockfile(lockfile)

    protocol = credentials["protocol"].lower()
    if protocol not in {"https", "http"}:
        raise SystemExit(f"Protocolo inesperado no lockfile: {protocol}")

    base_url = f"{protocol}://127.0.0.1:{credentials['port']}"
    authorization = auth_header(credentials["password"])

    print("=" * 96)
    print("TFT INSIGHT / ROADMAP 25.0B - SAFE LCU DISCOVERY")
    print("=" * 96)
    print(f"Lockfile : {lockfile}")
    print(f"Host     : {base_url}")
    print("Metodo   : GET somente")
    print("Memoria  : NAO")
    print("Injecao  : NAO")
    print("Input    : NAO")
    print("Token    : somente em memoria; NAO salvo")
    print()

    result: dict[str, Any] = {
        "captured_at": utc_stamp(),
        "policy": {
            "transport": "localhost only",
            "method": "GET only",
            "memory_reading": False,
            "process_injection": False,
            "input_automation": False,
            "credential_persistence": False,
        },
        "client": {
            "name": credentials["name"],
            "pid": credentials["pid"],
            "port": credentials["port"],
            "protocol": credentials["protocol"],
            "lockfile_path": str(lockfile),
            "password": "<REDACTED>",
        },
        "discovery": [],
        "safe_reads": [],
        "interesting_paths": [],
    }

    discovered_paths: set[str] = set()

    for endpoint in DISCOVERY_ENDPOINTS:
        item = safe_get(base_url, endpoint, authorization, args.timeout)
        clean = redact_session_payload(item)
        result["discovery"].append(clean)

        data = item.get("data")
        for path in extract_paths(data):
            discovered_paths.add(path)

    interesting = filter_interesting(sorted(discovered_paths))
    result["interesting_paths"] = interesting

    print(f"Paths descobertos : {len(discovered_paths)}")
    print(f"Paths interessantes: {len(interesting)}")

    for endpoint in SAFE_GET_ENDPOINTS:
        item = safe_get(base_url, endpoint, authorization, args.timeout)
        result["safe_reads"].append(redact_session_payload(item))

        status = item.get("status_code", "ERR")
        print(f"[GET] {endpoint:<45} {status}")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"lcu_discovery_{utc_stamp()}.json"

    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Resultado salvo: {output_path}")
    print()
    print("Top paths relacionados a TFT/gameflow/session:")
    for path in interesting[:80]:
        print(f"  {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
