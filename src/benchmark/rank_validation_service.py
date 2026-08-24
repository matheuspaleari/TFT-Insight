"""
Valida periodicamente o elo atual dos jogadores que compõem os benchmarks.
"""
from __future__ import annotations
from dataclasses import replace
from typing import Any
from src.benchmark.group_configuration import get_benchmark_group_configuration
from src.benchmark.player_catalog import BenchmarkPlayerCatalogRepository, utc_now_iso
from src.riot_client import RiotClient

class BenchmarkRankValidationService:
    def __init__(self, *, riot_client: RiotClient | None = None, repository: BenchmarkPlayerCatalogRepository | None = None) -> None:
        self.riot_client = riot_client or RiotClient()
        self.repository = repository or BenchmarkPlayerCatalogRepository()

    def validate(self, *, benchmark_id: str) -> dict[str, Any]:
        configuration = get_benchmark_group_configuration(benchmark_id)
        allowed_tiers = {rule.tier for rule in configuration.sampling_rules}
        players = self.repository.load(benchmark_id)
        if not players:
            raise FileNotFoundError(
                "Catálogo individual não encontrado para "
                f"'{benchmark_id}'. Gere o benchmark novamente."
            )

        checked = []
        changed = tier_changed = division_changed = lp_changed = outside_group = errors = 0

        for index, player in enumerate(players, 1):
            print(f"[{index}/{len(players)}] {player.riot_id}")
            try:
                entry = self.riot_client.get_ranked_tft_entry(
                    puuid=player.puuid,
                    queue_type="RANKED_TFT",
                )
            except Exception as error:
                errors += 1
                checked.append(player)
                print(f"  ERRO: {type(error).__name__}: {error}")
                continue

            if entry is None:
                errors += 1
                checked.append(player)
                print("  Sem RANKED_TFT atual.")
                continue

            tier = str(entry.get("tier", "")).strip().upper()
            division = str(entry.get("rank", "I")).strip().upper()
            league_points = int(entry.get("leaguePoints", 0))

            tier_diff = tier != player.current_tier
            division_diff = division != player.current_division
            lp_diff = league_points != player.current_league_points

            tier_changed += int(tier_diff)
            division_changed += int(division_diff)
            lp_changed += int(lp_diff)
            has_changed = tier_diff or division_diff or lp_diff

            history = list(player.rank_history)
            now = utc_now_iso()
            if has_changed:
                changed += 1
                history.append({
                    "checked_at": now,
                    "tier": tier,
                    "division": division,
                    "league_points": league_points,
                })

            if tier not in allowed_tiers:
                outside_group += 1

            checked.append(replace(
                player,
                current_tier=tier,
                current_division=division,
                current_league_points=league_points,
                rank_checked_at=now,
                rank_history=tuple(history),
            ))

            print(f"  {tier} {division} · {league_points} LP · {'ALTERADO' if has_changed else 'igual'}")

        self.repository.save(benchmark_id=benchmark_id, players=checked)
        total = len(checked)
        outside_ratio = outside_group / total if total else 0.0
        return {
            "benchmark_id": benchmark_id,
            "players": total,
            "changed": changed,
            "tier_changed": tier_changed,
            "division_changed": division_changed,
            "lp_changed": lp_changed,
            "outside_group": outside_group,
            "outside_group_ratio": round(outside_ratio, 4),
            "errors": errors,
        }
