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

DEFAULT_KEYWORDS = (
    "tft",
    "gameflow",
    "endofgame",
    "end-of-game",
    "match",
    "session",
    "spectat",
    "gameclient",
    "game-client",
    "playercredential",
    "player-credential",
)

SENSITIVE_KEYWORDS = (
    "token",
    "password",
    "auth",
    "credential",
    "machineid",
    "clipboard",
)

WRITE_PREFIXES = (
    "Post",
    "Put",
    "Patch",
    "Delete",
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


def collect_functions(help_data: Any) -> dict[str, str]:
    """
    O /help atual retorna um objeto com a chave 'functions'.
    Mantemos fallback recursivo para builds que encapsulem essa chave.
    """
    if not isinstance(help_data, dict):
        return {}

    direct = help_data.get("functions")
    if isinstance(direct, dict):
        return {
            str(name): str(description)
            for name, description in direct.items()
        }

    found: dict[str, str] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            functions = value.get("functions")
            if isinstance(functions, dict):
                for name, description in functions.items():
                    found[str(name)] = str(description)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(help_data)
    return found


def collect_events(help_data: Any) -> dict[str, str]:
    if not isinstance(help_data, dict):
        return {}

    found: dict[str, str] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            events = value.get("events")
            if isinstance(events, dict):
                for name, description in events.items():
                    found[str(name)] = str(description)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(help_data)
    return found


def is_get_function(name: str) -> bool:
    return name.startswith("Get") or name == "Help"


def contains_keyword(name: str, keywords: tuple[str, ...]) -> bool:
    compact = re.sub(r"[^a-z0-9]+", "", name.lower())
    return any(
        re.sub(r"[^a-z0-9]+", "", keyword.lower()) in compact
        for keyword in keywords
    )


def is_sensitive(name: str) -> bool:
    lower = name.lower()
    return any(keyword in lower for keyword in SENSITIVE_KEYWORDS)


def classify_function(
    name: str,
    description: str,
    keywords: tuple[str, ...],
) -> dict[str, Any]:
    method = "UNKNOWN"
    for prefix in ("Get", "Post", "Put", "Patch", "Delete"):
        if name.startswith(prefix):
            method = prefix.upper()
            break
    if name == "Help":
        method = "GET"

    relevant = contains_keyword(name, keywords)
    sensitive = is_sensitive(name)
    write = name.startswith(WRITE_PREFIXES)

    return {
        "name": name,
        "description": description,
        "method_family": method,
        "relevant": relevant,
        "sensitive_name": sensitive,
        "write_family": write,
        "safe_for_next_review": (
            method == "GET"
            and relevant
            and not sensitive
            and not write
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Mapeia o /help do LCU e extrai somente candidatos GET "
            "relevantes para revisao manual. Nao executa os candidatos."
        )
    )
    parser.add_argument("--lockfile")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--output",
        default="data/lcu_help_mapper",
    )
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=list(DEFAULT_KEYWORDS),
        help="Palavras usadas apenas para filtrar nomes retornados por /help.",
    )
    args = parser.parse_args()

    if args.timeout <= 0 or args.timeout > 10:
        raise SystemExit("Use --timeout entre 0 e 10 segundos.")

    keywords = tuple(args.keywords)

    lockfile = find_lockfile(args.lockfile)
    creds = parse_lockfile(lockfile)
    base_url = f"{creds['protocol']}://127.0.0.1:{creds['port']}"
    auth = auth_header(creds["password"])

    print("=" * 104)
    print("TFT INSIGHT / ROADMAP 25.0E - LCU /HELP MAPPER")
    print("=" * 104)
    print(f"Host     : {base_url}")
    print("Consulta : GET /help")
    print("Execucao : NAO testa endpoints encontrados")
    print("Memoria  : NAO")
    print("Injecao  : NAO")
    print("Input    : NAO")
    print()

    help_result = safe_get_help(
        base_url,
        auth,
        args.timeout,
    )

    status = help_result.get("status_code", "ERR")
    print(f"/help status: {status}")

    if not help_result.get("ok"):
        raise SystemExit(
            "Nao foi possivel ler /help. "
            "Confira o cliente/lockfile."
        )

    help_data = help_result.get("data")
    functions = collect_functions(help_data)
    events = collect_events(help_data)

    classified = [
        classify_function(name, description, keywords)
        for name, description in sorted(functions.items())
    ]

    get_functions = [
        item for item in classified
        if item["method_family"] == "GET"
    ]

    candidates = [
        item for item in classified
        if item["safe_for_next_review"]
    ]

    relevant_events = [
        {
            "name": name,
            "description": description,
        }
        for name, description in sorted(events.items())
        if contains_keyword(name, keywords)
        and not is_sensitive(name)
    ]

    print(f"Funcoes totais       : {len(classified)}")
    print(f"Familia GET          : {len(get_functions)}")
    print(f"Candidatos relevantes: {len(candidates)}")
    print(f"Eventos relevantes   : {len(relevant_events)}")
    print()

    print("TOP CANDIDATOS GET")
    print("-" * 104)
    for item in candidates[:120]:
        print(f"- {item['name']}")

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    stamp = utc_stamp()

    json_path = outdir / f"help_map_{stamp}.json"
    txt_path = outdir / f"help_map_{stamp}.txt"

    payload = {
        "captured_at": stamp,
        "policy": {
            "localhost_only": True,
            "help_get_only": True,
            "discovered_endpoints_executed": False,
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
        "keywords": list(keywords),
        "summary": {
            "functions_total": len(classified),
            "get_family_total": len(get_functions),
            "relevant_get_candidates": len(candidates),
            "relevant_events": len(relevant_events),
        },
        "get_candidates": candidates,
        "relevant_events": relevant_events,
        "help_snapshot": redact(help_data),
    }

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "TFT INSIGHT / ROADMAP 25.0E - LCU /HELP MAPPER",
        "=" * 104,
        f"captured_at: {stamp}",
        "",
        f"Funcoes totais        : {len(classified)}",
        f"Familia GET           : {len(get_functions)}",
        f"Candidatos relevantes : {len(candidates)}",
        f"Eventos relevantes    : {len(relevant_events)}",
        "",
        "CANDIDATOS GET PARA REVISAO MANUAL",
        "-" * 104,
    ]

    for item in candidates:
        desc = item["description"].strip()
        if desc:
            lines.append(f"{item['name']} :: {desc}")
        else:
            lines.append(item["name"])

    lines.extend([
        "",
        "EVENTOS RELEVANTES",
        "-" * 104,
    ])

    for item in relevant_events:
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
        "Nenhum endpoint descoberto foi chamado. "
        "O proximo passo e revisar esta lista."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
