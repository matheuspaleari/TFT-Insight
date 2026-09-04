from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import urllib3


HOST = "127.0.0.1"
PORT = 2999
BASE_URL = f"https://{HOST}:{PORT}"

ENDPOINTS = {
    "openapi": "/swagger/v3/openapi.json",
    "allgamedata": "/liveclientdata/allgamedata",
}

DEFAULT_INTERVAL_SECONDS = 15.0
DEFAULT_TIMEOUT_SECONDS = 3.0

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def get_json(path: str, timeout: float) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"

    try:
        response = requests.get(
            url,
            timeout=timeout,
            verify=False,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return {
            "ok": False,
            "url": url,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result: dict[str, Any] = {
        "ok": response.ok,
        "url": url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
    }

    try:
        result["data"] = response.json()
    except ValueError:
        result["text_preview"] = response.text[:1000]

    return result


def write_snapshot(output_dir: Path, payload: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{payload['captured_at']}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def capture(output_dir: Path, timeout: float) -> Path:
    payload: dict[str, Any] = {
        "captured_at": utc_stamp(),
        "policy": {
            "transport": "HTTPS localhost only",
            "host": HOST,
            "port": PORT,
            "method": "GET only",
            "memory_reading": False,
            "process_injection": False,
            "input_automation": False,
        },
        "endpoints": {},
    }

    for name, path in ENDPOINTS.items():
        payload["endpoints"][name] = get_json(path, timeout)

    return write_snapshot(output_dir, payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "POC seguro do TFT Insight: consulta somente APIs HTTPS locais "
            "em 127.0.0.1:2999 e grava as respostas para analise pos-jogo."
        )
    )
    parser.add_argument(
        "--output",
        default="data/live_probe",
        help="Diretorio dos snapshots. Padrao: data/live_probe",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Intervalo entre snapshots no modo watch.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout HTTP por endpoint.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Faz apenas uma captura e encerra.",
    )
    parser.add_argument(
        "--max-snapshots",
        type=int,
        default=0,
        help="Limite no modo watch; 0 = ate Ctrl+C.",
    )

    args = parser.parse_args()

    if args.interval < 5:
        raise SystemExit("Por seguranca, use --interval >= 5 segundos.")

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    output_dir = Path(args.output)

    print("=" * 92)
    print("TFT INSIGHT / ROADMAP 25.0A - SAFE LIVE API PROBE")
    print("=" * 92)
    print(f"Destino : {output_dir.resolve()}")
    print(f"Host    : {BASE_URL}")
    print("Metodo  : GET somente")
    print("Memoria : NAO")
    print("Injecao : NAO")
    print("Input   : NAO")
    print()

    captured = 0

    try:
        while True:
            path = capture(output_dir, args.timeout)
            captured += 1
            print(f"[{captured:03d}] snapshot salvo: {path}")

            if args.once:
                break

            if args.max_snapshots and captured >= args.max_snapshots:
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print()
        print("Probe encerrado pelo usuario.")

    print(f"Snapshots capturados: {captured}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
