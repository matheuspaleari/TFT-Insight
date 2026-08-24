from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rank_history.service import RankObservationService
from src.services.player_analysis_service import PlayerAnalysisService


def main():
    checks = []

    player_source = (
        ROOT / "src/services/player_analysis_service.py"
    ).read_text(encoding="utf-8")
    rank_source = (
        ROOT / "src/rank_history/service.py"
    ).read_text(encoding="utf-8")

    checks += [
        ("Player Analysis usa entrada RANKED_TFT completa", "get_ranked_tft_entry" in player_source),
        ("Double Up não é usado", 'queue_type="RANKED_TFT"' in player_source),
        ("Benchmark usa tier real", "current_rank=benchmark_tier" in player_source),
        ("UI recebe elo completo via current_rank", "current_rank=current_rank_display" in player_source),
        ("Elo mostra divisão", "entry.get(\"rank\"" in player_source),
        ("Elo mostra LP", "leaguePoints" in player_source),
        ("Rank history conectado ao analyze", ".record_resolved(" in player_source),
        ("Busca janela de 100 para histórico", "RankObservationService.DEFAULT_SCAN_LIMIT" in player_source),
        ("Análise respeita match_count", "match_ids = recent_match_ids[:match_count]" in player_source),
        ("Serviço evita chamadas Riot duplicadas", "def record_resolved(" in rank_source),
        ("Snapshots idênticos são deduplicados", "persisted_now" in rank_source and "_same_state" in rank_source),
    ]

    resolve = RankObservationService._resolve_new_matches
    checks += [
        (
            "1 nova partida => EXACT",
            resolve(
                current_match_ids=["B", "A"],
                previous={"latest_match_id": "A"},
            ) == (["B"], "EXACT"),
        ),
        (
            "3 novas partidas => INTERVAL",
            resolve(
                current_match_ids=["D", "C", "B", "A"],
                previous={"latest_match_id": "A"},
            ) == (["D", "C", "B"], "INTERVAL"),
        ),
        (
            "Corte fora da janela => TRUNCATED",
            resolve(
                current_match_ids=["D", "C"],
                previous={"latest_match_id": "A"},
            ) == (["D", "C"], "TRUNCATED"),
        ),
        (
            "Formatação Emerald IV 0 LP",
            PlayerAnalysisService._format_rank_display(
                {"tier": "EMERALD", "rank": "IV", "leaguePoints": 0}
            ) == "EMERALD IV · 0 LP",
        ),
    ]

    print("=" * 82)
    print("TFT INSIGHT - RANK + PLAYER ANALYSIS INTEGRATION V1")
    print("=" * 82)

    passed = 0
    for i, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print(f"\n[{i}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print("\n" + "=" * 82)
    print(f"PASSARAM: {passed}/{len(checks)}")
    if passed == len(checks):
        print("RANK + PLAYER ANALYSIS INTEGRATION V1: VALIDADA")
        raise SystemExit(0)

    print("RANK + PLAYER ANALYSIS INTEGRATION V1: AJUSTE NECESSÁRIO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
