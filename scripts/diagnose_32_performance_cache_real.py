from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from partner_platform.services.api_client import DashboardApiClient


MODULES = (
    ("composition", "composition_intelligence"),
    ("contest", "contest_intelligence"),
    ("economy", "economy_intelligence"),
    ("carry_item", "carry_item_intelligence"),
)


def run_pass(
    *,
    client: DashboardApiClient,
    game_name: str,
    tag_line: str,
    match_count: int,
) -> dict:
    result = {}

    for label, method_name in MODULES:
        method = getattr(
            client,
            method_name,
        )

        started = time.perf_counter()

        try:
            payload = method(
                game_name=game_name,
                tag_line=tag_line,
                match_count=match_count,
            )

            collection = payload.get(
                "collection",
                {},
            ) or {}

            result[label] = {
                "ok": True,
                "elapsed_seconds": round(
                    time.perf_counter() - started,
                    3,
                ),
                "valid_matches": collection.get("valid_matches"),
                "candidate_ids_received": collection.get("candidate_ids_received"),
                "candidate_ids_considered": collection.get("candidate_ids_considered"),
                "cached_matches_used": collection.get("cached_matches_used"),
                "new_matches_downloaded": collection.get("new_matches_downloaded"),
                "failed_matches": collection.get("failed_matches"),
                "cache_hit_rate": collection.get("cache_hit_rate"),
                "load_elapsed_seconds": collection.get("load_elapsed_seconds"),
                "stopped_after_target": collection.get("stopped_after_target"),
            }

        except Exception as error:
            result[label] = {
                "ok": False,
                "elapsed_seconds": round(
                    time.perf_counter() - started,
                    3,
                ),
                "error": f"{type(error).__name__}: {error}",
            }

    return result


def main() -> None:
    game_name = input(
        "Riot ID (Game Name): "
    ).strip()

    tag_line = input(
        "Tag: "
    ).strip()

    raw_count = input(
        "Partidas [10]: "
    ).strip()

    match_count = (
        int(raw_count)
        if raw_count
        else 10
    )

    client = DashboardApiClient(
        base_url=os.getenv(
            "TFT_INSIGHT_API_BASE_URL",
            "http://127.0.0.1:8000",
        ),
        api_key=os.getenv(
            "TFT_INSIGHT_API_KEY",
            "",
        ),
        timeout=300.0,
    )

    print()
    print("=" * 112)
    print("#32 PERFORMANCE + CACHE + ERROS - DIAGNÓSTICO REAL")
    print("=" * 112)
    print(f"Jogador          : {game_name}#{tag_line}")
    print(f"Partidas/módulo  : {match_count}")

    print()
    print("PASSO 1 — PRIMEIRA PASSAGEM")
    print("-" * 112)

    first = run_pass(
        client=client,
        game_name=game_name,
        tag_line=tag_line,
        match_count=match_count,
    )

    for label, item in first.items():
        print(
            f"{label:<14} | "
            f"{'OK' if item.get('ok') else 'ERRO':<4} | "
            f"{item.get('elapsed_seconds', 0):>7.3f}s | "
            f"considerados={item.get('candidate_ids_considered', '-')} | "
            f"download={item.get('new_matches_downloaded', '-')} | "
            f"cache={item.get('cache_hit_rate', '-')}% | "
            f"stop={item.get('stopped_after_target', '-')}"
        )

    print()
    print("PASSO 2 — SEGUNDA PASSAGEM (WARM)")
    print("-" * 112)

    second = run_pass(
        client=client,
        game_name=game_name,
        tag_line=tag_line,
        match_count=match_count,
    )

    for label, item in second.items():
        print(
            f"{label:<14} | "
            f"{'OK' if item.get('ok') else 'ERRO':<4} | "
            f"{item.get('elapsed_seconds', 0):>7.3f}s | "
            f"considerados={item.get('candidate_ids_considered', '-')} | "
            f"download={item.get('new_matches_downloaded', '-')} | "
            f"cache={item.get('cache_hit_rate', '-')}% | "
            f"stop={item.get('stopped_after_target', '-')}"
        )

    print()
    print("COMPARAÇÃO")
    print("-" * 112)

    all_ok = True
    warm_cache_ok = True

    for label, _ in MODULES:
        a = first.get(label, {})
        b = second.get(label, {})

        if not a.get("ok") or not b.get("ok"):
            all_ok = False
            print(
                f"{label:<14}: ERRO em uma das passagens"
            )
            continue

        first_time = float(
            a.get("elapsed_seconds", 0)
            or 0
        )

        second_time = float(
            b.get("elapsed_seconds", 0)
            or 0
        )

        second_downloads = int(
            b.get("new_matches_downloaded", 0)
            or 0
        )

        if second_downloads != 0:
            warm_cache_ok = False

        improvement = (
            (
                first_time - second_time
            )
            / first_time
            * 100.0
            if first_time > 0
            else 0.0
        )

        print(
            f"{label:<14}: "
            f"{first_time:.3f}s -> {second_time:.3f}s "
            f"({improvement:+.1f}%) | "
            f"warm_download={second_downloads}"
        )

    output_dir = (
        ROOT
        / "data/diagnostics/performance_cache"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    output = (
        output_dir
        / f"performance_cache_{timestamp}.json"
    )

    output.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "player": {
                    "game_name": game_name,
                    "tag_line": tag_line,
                },
                "match_count": match_count,
                "first": first,
                "second": second,
                "summary": {
                    "all_modules_ok": all_ok,
                    "warm_cache_zero_downloads": warm_cache_ok,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("RESUMO")
    print("-" * 112)
    print(
        f"Módulos OK               : "
        f"{'OK' if all_ok else 'ERRO'}"
    )
    print(
        f"Warm sem novos downloads : "
        f"{'OK' if warm_cache_ok else 'REVISAR'}"
    )
    print(
        f"Relatório                : {output}"
    )

    print()
    print("=" * 112)

    if all_ok and warm_cache_ok:
        print(
            "#32 PERFORMANCE + CACHE + ERROS: DIAGNÓSTICO VALIDADO"
        )
    else:
        print(
            "#32 PERFORMANCE + CACHE + ERROS: REVISAR"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
