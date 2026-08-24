from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rank_history.service import RankObservationService


def main():
    resolve = RankObservationService._resolve_new_matches

    cases = [
        (
            "Primeira consulta cria baseline",
            resolve(current_match_ids=["M3", "M2", "M1"], previous=None),
            ([], "BASELINE"),
        ),
        (
            "Sem nova partida",
            resolve(
                current_match_ids=["M3", "M2", "M1"],
                previous={"latest_match_id": "M3"},
            ),
            ([], "NO_NEW_MATCHES"),
        ),
        (
            "Uma nova partida é EXACT",
            resolve(
                current_match_ids=["M4", "M3", "M2", "M1"],
                previous={"latest_match_id": "M3"},
            ),
            (["M4"], "EXACT"),
        ),
        (
            "Quatro novas partidas são INTERVAL",
            resolve(
                current_match_ids=["M7", "M6", "M5", "M4", "M3"],
                previous={"latest_match_id": "M3"},
            ),
            (["M7", "M6", "M5", "M4"], "INTERVAL"),
        ),
        (
            "Partida anterior fora da janela é TRUNCATED",
            resolve(
                current_match_ids=["M9", "M8", "M7"],
                previous={"latest_match_id": "M3"},
            ),
            (["M9", "M8", "M7"], "TRUNCATED"),
        ),
    ]

    checks = []
    for name, actual, expected in cases:
        checks.append((name, actual == expected))

    source = (
        ROOT / "src/rank_history/service.py"
    ).read_text(encoding="utf-8")

    checks += [
        ("Usa somente RANKED_TFT", 'QUEUE_TYPE = "RANKED_TFT"' in source),
        ("Persiste rank_observations.json", 'rank_observations.json' in source),
        ("Registra contagem entre snapshots", 'matches_since_previous_rank_snapshot' in source),
        ("Registra IDs do intervalo", '"new_match_ids"' in source),
        ("Não chama associação de rank_at_match", "rank_at_match" not in source),
        ("Registra elo observado", '"tier"' in source and '"division"' in source),
        ("Registra LP observado", '"league_points"' in source),
    ]

    print("=" * 82)
    print("TFT INSIGHT - RANK OBSERVATION HISTORY V1")
    print("=" * 82)

    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\n[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print("\n" + "=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed == len(checks):
        print("RANK OBSERVATION HISTORY V1: VALIDADO")
        raise SystemExit(0)

    print("RANK OBSERVATION HISTORY V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
