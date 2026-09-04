from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TARGET_IMAGE = "League of Legends.exe"


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def run(cmd: list[str]) -> str:
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return completed.stdout


def get_target_pids() -> set[int]:
    output = run([
        "tasklist",
        "/FI", f"IMAGENAME eq {TARGET_IMAGE}",
        "/FO", "CSV",
        "/NH",
    ])

    pids: set[int] = set()

    for row in csv.reader(io.StringIO(output)):
        if len(row) < 2:
            continue

        image = row[0].strip()
        pid_raw = row[1].strip()

        if image.lower() != TARGET_IMAGE.lower():
            continue

        try:
            pids.add(int(pid_raw))
        except ValueError:
            pass

    return pids


def parse_endpoint(value: str) -> dict[str, Any]:
    value = value.strip()

    if value.startswith("["):
        host, _, port = value.rpartition("]:")
        host = host + "]"
    else:
        host, _, port = value.rpartition(":")

    try:
        port_num = int(port)
    except ValueError:
        port_num = None

    return {
        "raw": value,
        "host": host,
        "port": port_num,
    }


def get_process_tcp_rows(pids: set[int]) -> list[dict[str, Any]]:
    output = run(["netstat", "-ano", "-p", "tcp"])
    rows: list[dict[str, Any]] = []

    for line in output.splitlines():
        parts = line.split()

        if len(parts) < 5:
            continue

        if parts[0].upper() != "TCP":
            continue

        local_raw = parts[1]
        remote_raw = parts[2]
        state = parts[3]

        try:
            pid = int(parts[4])
        except ValueError:
            continue

        if pid not in pids:
            continue

        local = parse_endpoint(local_raw)
        remote = parse_endpoint(remote_raw)

        rows.append({
            "pid": pid,
            "protocol": "TCP",
            "local": local,
            "remote": remote,
            "state": state,
        })

    return rows


def is_loopback(host: str) -> bool:
    normalized = host.strip("[]").lower()
    return normalized in {"127.0.0.1", "::1", "localhost"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Lista somente conexoes/portas TCP pertencentes ao processo "
            "'League of Legends.exe'. Nao abre sockets e nao faz probes HTTP."
        )
    )
    parser.add_argument(
        "--output",
        default="data/process_port_discovery",
    )
    args = parser.parse_args()

    print("=" * 110)
    print("TFT INSIGHT / ROADMAP 25.0J - PROCESS-BOUND LOCAL PORT DISCOVERY")
    print("=" * 110)
    print(f"Processo alvo : {TARGET_IMAGE}")
    print("Fonte         : tasklist + netstat")
    print("Port scan     : NAO")
    print("HTTP probe    : NAO")
    print("Memoria       : NAO")
    print("Injecao       : NAO")
    print("Sniffing      : NAO")
    print("Input         : NAO")
    print()

    pids = get_target_pids()

    if not pids:
        raise SystemExit(
            "League of Legends.exe nao foi encontrado. "
            "Rode este script enquanto estiver dentro da partida."
        )

    rows = get_process_tcp_rows(pids)

    listeners = [
        row for row in rows
        if row["state"].upper() == "LISTENING"
    ]

    loopback_listeners = [
        row for row in listeners
        if is_loopback(row["local"]["host"])
    ]

    all_local_ports = sorted({
        row["local"]["port"]
        for row in rows
        if row["local"]["port"] is not None
    })

    listening_ports = sorted({
        row["local"]["port"]
        for row in listeners
        if row["local"]["port"] is not None
    })

    loopback_ports = sorted({
        row["local"]["port"]
        for row in loopback_listeners
        if row["local"]["port"] is not None
    })

    print("PIDs encontrados:", ", ".join(str(x) for x in sorted(pids)))
    print(f"Conexoes TCP do processo : {len(rows)}")
    print(f"Listeners                : {len(listeners)}")
    print(f"Listeners localhost      : {len(loopback_listeners)}")
    print()

    if loopback_listeners:
        print("PORTAS LOCALHOST EM LISTENING")
        print("-" * 110)
        for row in loopback_listeners:
            print(
                f"PID={row['pid']} "
                f"{row['local']['host']}:{row['local']['port']} "
                f"state={row['state']}"
            )
    else:
        print("Nenhuma porta localhost em LISTENING foi encontrada.")

    payload = {
        "captured_at": stamp(),
        "policy": {
            "process_bound_only": True,
            "port_scan": False,
            "http_probe": False,
            "memory_reading": False,
            "process_injection": False,
            "packet_sniffing": False,
            "input_automation": False,
        },
        "target_image": TARGET_IMAGE,
        "pids": sorted(pids),
        "summary": {
            "tcp_rows": len(rows),
            "listeners": len(listeners),
            "loopback_listeners": len(loopback_listeners),
            "all_local_ports": all_local_ports,
            "listening_ports": listening_ports,
            "loopback_listening_ports": loopback_ports,
        },
        "loopback_listeners": loopback_listeners,
        "listeners": listeners,
        "all_process_tcp_rows": rows,
    }

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    path = outdir / f"process_ports_{stamp()}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Resultado salvo: {path}")

    if loopback_ports:
        print()
        print(
            "Proximo passo: revisar estas portas antes de qualquer GET. "
            "Nao teste endpoints aleatorios ainda."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
