from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from dotenv import load_dotenv


DOCUMENTED_PLATFORMS = {
    "br1",
    "eun1",
    "euw1",
    "jp1",
    "kr",
    "la1",
    "la2",
    "na1",
    "oc1",
    "tr1",
    "ru",
    "ph2",
    "sg2",
    "th2",
    "tw2",
    "vn2",
}

REGIONAL_ROUTES = {
    "americas",
    "asia",
    "europe",
}

DEFAULT_TIMEOUT = 5.0


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def safe_get(
    url: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    try:
        response = requests.get(
            url,
            headers={
                "X-Riot-Token": api_key,
                "Accept": "application/json",
            },
            timeout=timeout,
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
        "rate_limit_type": response.headers.get("x-rate-limit-type"),
        "retry_after": response.headers.get("retry-after"),
    }

    try:
        result["data"] = response.json()
    except ValueError:
        result["text_preview"] = response.text[:1000]

    return result


def resolve_puuid(
    game_name: str,
    tag_line: str,
    region: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    encoded_name = quote(game_name, safe="")
    encoded_tag = quote(tag_line, safe="")
    url = (
        f"https://{region}.api.riotgames.com"
        f"/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
    )
    result = safe_get(url, api_key, timeout)
    result["request_kind"] = "account_by_riot_id"
    result["host"] = region
    return result


def spectator_current_game(
    puuid: str,
    platform: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    encoded_puuid = quote(puuid, safe="")
    url = (
        f"https://{platform}.api.riotgames.com"
        f"/lol/spectator/tft/v5/active-games/by-puuid/{encoded_puuid}"
    )
    result = safe_get(url, api_key, timeout)
    result["request_kind"] = "spectator_tft_current_game"
    result["host"] = platform
    return result


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            lower = key.lower()
            if "token" in lower or "password" in lower or "secret" in lower:
                cleaned[key] = "<REDACTED>"
            else:
                cleaned[key] = redact(item)
        return cleaned

    if isinstance(value, list):
        return [redact(item) for item in value]

    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Probe seguro do spectator-tft-v5. "
            "Usa somente GETs oficiais da Riot API."
        )
    )
    parser.add_argument(
        "--riot-id",
        required=True,
        help="Game Name do Riot ID.",
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Tag Line do Riot ID.",
    )
    parser.add_argument(
        "--platform",
        default="br1",
        help="Platform route documentado. Ex.: br1, na1, euw1.",
    )
    parser.add_argument(
        "--region",
        default="americas",
        help="Regional route para account-v1. Ex.: americas.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
    )
    parser.add_argument(
        "--output",
        default="data/spectator_probe",
    )
    args = parser.parse_args()

    platform = args.platform.lower()
    region = args.region.lower()

    if platform not in DOCUMENTED_PLATFORMS:
        raise SystemExit(
            f"Platform '{platform}' nao esta na lista documentada. "
            "Nao vamos adivinhar rotas como PBE1."
        )

    if region not in REGIONAL_ROUTES:
        raise SystemExit(
            f"Region '{region}' nao suportada pelo probe."
        )

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    load_dotenv()
    api_key = os.getenv("RIOT_API_KEY", "").strip()

    if not api_key:
        raise SystemExit(
            "RIOT_API_KEY nao encontrada no .env local."
        )

    print("=" * 100)
    print("TFT INSIGHT / ROADMAP 25.0D - SAFE SPECTATOR-TFT-V5 PROBE")
    print("=" * 100)
    print(f"Riot ID  : {args.riot_id}#{args.tag}")
    print(f"Platform : {platform}")
    print(f"Region   : {region}")
    print("Metodo   : GET somente")
    print("API      : oficial Riot")
    print("Memoria  : NAO")
    print("Injecao  : NAO")
    print("Input    : NAO")
    print("API key  : lida do .env; NAO salva")
    print()

    account = resolve_puuid(
        args.riot_id,
        args.tag,
        region,
        api_key,
        args.timeout,
    )

    print(
        f"[account-v1] status="
        f"{account.get('status_code', 'ERR')}"
    )

    account_data = account.get("data")

    if not account.get("ok") or not isinstance(account_data, dict):
        payload = {
            "captured_at": utc_stamp(),
            "policy": {
                "official_riot_api_only": True,
                "get_only": True,
                "memory_reading": False,
                "process_injection": False,
                "input_automation": False,
                "api_key_persisted": False,
            },
            "riot_id": {
                "game_name": args.riot_id,
                "tag_line": args.tag,
            },
            "platform": platform,
            "region": region,
            "account": redact(account),
            "spectator": None,
        }

        outdir = Path(args.output)
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"spectator_probe_{utc_stamp()}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"Resultado salvo: {path}")
        return 2

    puuid = account_data.get("puuid")

    if not puuid:
        raise SystemExit("account-v1 respondeu sem PUUID.")

    spectator = spectator_current_game(
        puuid,
        platform,
        api_key,
        args.timeout,
    )

    print(
        f"[spectator-tft-v5] status="
        f"{spectator.get('status_code', 'ERR')}"
    )

    payload = {
        "captured_at": utc_stamp(),
        "policy": {
            "official_riot_api_only": True,
            "get_only": True,
            "memory_reading": False,
            "process_injection": False,
            "input_automation": False,
            "api_key_persisted": False,
        },
        "riot_id": {
            "game_name": args.riot_id,
            "tag_line": args.tag,
        },
        "platform": platform,
        "region": region,
        "account": {
            "ok": account.get("ok"),
            "status_code": account.get("status_code"),
            "puuid": puuid,
            "gameName": account_data.get("gameName"),
            "tagLine": account_data.get("tagLine"),
        },
        "spectator": redact(spectator),
    }

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"spectator_probe_{utc_stamp()}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Resultado salvo: {path}")

    status = spectator.get("status_code")

    if status == 200:
        print("Partida TFT ativa encontrada.")
        return 0

    if status == 404:
        print(
            "Nenhuma partida TFT ativa encontrada para esse PUUID "
            "nessa platform route."
        )
        return 0

    if status in {401, 403}:
        print(
            "Chave sem autorizacao/expirada ou acesso indisponivel "
            "para esse endpoint."
        )
        return 3

    if status == 429:
        print("Rate limit atingido. Respeite Retry-After.")
        return 4

    print("Resposta inesperada; revise o JSON salvo.")
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
