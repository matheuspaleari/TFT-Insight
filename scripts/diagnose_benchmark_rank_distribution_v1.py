from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.riot_client import RiotClient


BENCHMARK_DIR = ROOT / "data" / "benchmark"
OUTPUT_DIR = ROOT / "data" / "benchmark" / "rank_audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

JSON_OUTPUT = OUTPUT_DIR / "benchmark_player_ranks.json"
CSV_OUTPUT = OUTPUT_DIR / "benchmark_player_ranks.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "benchmark_rank_summary.json"
CHECKPOINT_OUTPUT = OUTPUT_DIR / "benchmark_rank_checkpoint.json"

KNOWN_BENCHMARKS = (
    "novice",
    "intermediate",
    "advanced",
    "expert",
    "elite",
    "challenger_br",
)

# Catálogo histórico atual do projeto.
CATALOG_TO_BENCHMARK = {
    "challenger_player_catalog": "challenger_br",
    "challenger_br_player_catalog": "challenger_br",
}

PLAYER_NAME_KEYS = (
    "game_name",
    "gameName",
    "summoner_name",
    "summonerName",
    "name",
)

TAG_KEYS = (
    "tag_line",
    "tagLine",
    "tag",
)

PUUID_KEYS = (
    "puuid",
    "player_puuid",
    "playerPuuid",
)


class BenchmarkRankAudit:
    def __init__(self) -> None:
        self.riot = RiotClient()
        self.checkpoint = self._load_checkpoint()

    def run(self) -> None:
        print("=" * 88)
        print("TFT INSIGHT - AUDITORIA DE ELOS DOS BENCHMARKS V1")
        print("=" * 88)
        print()
        print(f"Diretório de benchmarks: {BENCHMARK_DIR}")
        print()

        identities, files_report = self._discover_players()

        print("DESCOBERTA DE JOGADORES")
        print("-" * 88)
        for benchmark_id in KNOWN_BENCHMARKS:
            count = sum(1 for item in identities if item["benchmark_id"] == benchmark_id)
            status = "identidades encontradas" if count else "sem identidades individuais"
            print(f"{benchmark_id:<18} : {count:>4} jogador(es) | {status}")

        print()
        print(f"Jogadores únicos para consultar: {len(identities)}")

        if not identities:
            print()
            print("Nenhuma identidade individual foi encontrada nos arquivos atuais.")
            print("Os benchmarks agregados preservam métricas, mas não necessariamente os jogadores.")
            self._write_empty_summary(files_report)
            return

        results = []
        for index, identity in enumerate(identities, 1):
            label = self._identity_label(identity)
            print()
            print(f"[{index}/{len(identities)}] {identity['benchmark_id']} | {label}")

            try:
                result = self._resolve_rank(identity)
                print(
                    "  -> "
                    + (
                        f"{result['tier']} {result['division']} · {result['league_points']} LP"
                        if result["ranked"]
                        else "sem RANKED_TFT atual"
                    )
                )
            except Exception as exc:
                result = {
                    **identity,
                    "resolved_game_name": identity.get("game_name"),
                    "resolved_tag_line": identity.get("tag_line"),
                    "resolved_puuid": identity.get("puuid"),
                    "ranked": False,
                    "tier": None,
                    "division": None,
                    "league_points": None,
                    "wins": None,
                    "losses": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(f"  -> ERRO: {result['error']}")

            results.append(result)
            self._save_checkpoint_result(identity, result)

        self._write_outputs(results, files_report)
        self._print_summary(results, files_report)

    def _discover_players(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not BENCHMARK_DIR.exists():
            raise RuntimeError(f"Diretório não encontrado: {BENCHMARK_DIR}")

        identities: list[dict[str, Any]] = []
        files_report: list[dict[str, Any]] = []

        json_files = sorted(BENCHMARK_DIR.glob("*.json"))

        for path in json_files:
            if path.parent == OUTPUT_DIR:
                continue

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                files_report.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "benchmark_id": self._benchmark_from_file(path),
                        "players_found": 0,
                        "status": "INVALID_JSON",
                        "error": str(exc),
                    }
                )
                continue

            benchmark_id = self._benchmark_from_payload(path, data)
            discovered = self._extract_identities(
                data,
                benchmark_id=benchmark_id,
                source_file=str(path.relative_to(ROOT)),
            )

            # Evita considerar o próprio benchmark agregado como um jogador.
            discovered = [item for item in discovered if self._has_real_identity(item)]
            identities.extend(discovered)

            files_report.append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "benchmark_id": benchmark_id,
                    "players_found": len(discovered),
                    "status": "OK",
                }
            )

        identities = self._deduplicate(identities)
        return identities, files_report

    def _extract_identities(
        self,
        node: Any,
        *,
        benchmark_id: str,
        source_file: str,
    ) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []

        if isinstance(node, dict):
            # Se um nó interno declarar explicitamente o benchmark, preservamos.
            local_benchmark = str(
                node.get("benchmark_id")
                or node.get("benchmark")
                or benchmark_id
            ).strip()
            if local_benchmark not in KNOWN_BENCHMARKS:
                local_benchmark = benchmark_id

            identity = self._identity_from_dict(
                node,
                benchmark_id=local_benchmark,
                source_file=source_file,
            )
            if identity is not None:
                found.append(identity)

            for value in node.values():
                found.extend(
                    self._extract_identities(
                        value,
                        benchmark_id=local_benchmark,
                        source_file=source_file,
                    )
                )

        elif isinstance(node, list):
            for value in node:
                found.extend(
                    self._extract_identities(
                        value,
                        benchmark_id=benchmark_id,
                        source_file=source_file,
                    )
                )

        return found

    def _identity_from_dict(
        self,
        data: dict[str, Any],
        *,
        benchmark_id: str,
        source_file: str,
    ) -> dict[str, Any] | None:
        puuid = self._first_text(data, PUUID_KEYS)
        game_name = self._first_text(data, PLAYER_NAME_KEYS)
        tag_line = self._first_text(data, TAG_KEYS)

        # Nome solto não basta: métricas podem ter campos "name".
        has_riot_id = bool(game_name and tag_line)
        has_puuid = bool(puuid)

        if not has_riot_id and not has_puuid:
            return None

        matches_played = data.get("matches_played")
        if not isinstance(matches_played, int):
            matches_played = data.get("matches") if isinstance(data.get("matches"), int) else None

        return {
            "benchmark_id": benchmark_id,
            "source_file": source_file,
            "game_name": game_name,
            "tag_line": tag_line,
            "puuid": puuid,
            "matches_played_in_benchmark": matches_played,
        }

    def _resolve_rank(self, identity: dict[str, Any]) -> dict[str, Any]:
        checkpoint_key = self._checkpoint_key(identity)
        cached = self.checkpoint.get("players", {}).get(checkpoint_key)
        if isinstance(cached, dict) and cached.get("completed"):
            print("  -> checkpoint reutilizado")
            return cached["result"]

        puuid = identity.get("puuid")
        game_name = identity.get("game_name")
        tag_line = identity.get("tag_line")

        if puuid:
            account = self.riot.get_account_by_puuid(puuid=puuid)
        else:
            account = self.riot.get_account(
                game_name=str(game_name),
                tag_line=str(tag_line),
            )

        resolved_puuid = str(account.get("puuid", "")).strip()
        if not resolved_puuid:
            raise RuntimeError("Conta resolvida sem PUUID.")

        ranked = self.riot.get_ranked_tft_entry(
            puuid=resolved_puuid,
            queue_type="RANKED_TFT",
        )

        return {
            **identity,
            "resolved_game_name": account.get("gameName") or game_name,
            "resolved_tag_line": account.get("tagLine") or tag_line,
            "resolved_puuid": resolved_puuid,
            "ranked": ranked is not None,
            "tier": self._upper(ranked, "tier"),
            "division": self._upper(ranked, "rank"),
            "league_points": self._integer(ranked, "leaguePoints"),
            "wins": self._integer(ranked, "wins"),
            "losses": self._integer(ranked, "losses"),
            "error": None,
        }

    def _write_outputs(
        self,
        results: list[dict[str, Any]],
        files_report: list[dict[str, Any]],
    ) -> None:
        JSON_OUTPUT.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        fieldnames = [
            "benchmark_id",
            "source_file",
            "resolved_game_name",
            "resolved_tag_line",
            "resolved_puuid",
            "matches_played_in_benchmark",
            "ranked",
            "tier",
            "division",
            "league_points",
            "wins",
            "losses",
            "error",
        ]

        with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for item in results:
                writer.writerow({key: item.get(key) for key in fieldnames})

        summary = self._build_summary(results, files_report)
        SUMMARY_OUTPUT.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _build_summary(
        self,
        results: list[dict[str, Any]],
        files_report: list[dict[str, Any]],
    ) -> dict[str, Any]:
        by_benchmark: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in results:
            by_benchmark[item["benchmark_id"]].append(item)

        benchmark_summaries = {}
        for benchmark_id in KNOWN_BENCHMARKS:
            items = by_benchmark.get(benchmark_id, [])
            ranked_items = [item for item in items if item.get("ranked")]
            tier_counts = Counter(item.get("tier") for item in ranked_items if item.get("tier"))

            benchmark_summaries[benchmark_id] = {
                "players_identified": len(items),
                "players_with_ranked_tft": len(ranked_items),
                "players_without_ranked_tft": sum(1 for item in items if not item.get("ranked") and not item.get("error")),
                "errors": sum(1 for item in items if item.get("error")),
                "tier_distribution": dict(sorted(tier_counts.items())),
                "min_tier": self._min_tier(tier_counts),
                "max_tier": self._max_tier(tier_counts),
            }

        return {
            "benchmarks": benchmark_summaries,
            "files": files_report,
            "important": (
                "Os elos consultados são elos atuais no momento desta auditoria. "
                "Eles não provam o elo histórico do jogador quando o benchmark foi coletado."
            ),
        }

    def _print_summary(
        self,
        results: list[dict[str, Any]],
        files_report: list[dict[str, Any]],
    ) -> None:
        summary = self._build_summary(results, files_report)

        print()
        print("=" * 88)
        print("DISTRIBUIÇÃO DE ELOS POR BENCHMARK")
        print("=" * 88)

        for benchmark_id in KNOWN_BENCHMARKS:
            item = summary["benchmarks"][benchmark_id]
            print()
            print(f"BENCHMARK: {benchmark_id}")
            print(f"  Jogadores identificados : {item['players_identified']}")
            print(f"  RANKED_TFT encontrado    : {item['players_with_ranked_tft']}")
            print(f"  Menor tier observado     : {item['min_tier'] or '-'}")
            print(f"  Maior tier observado     : {item['max_tier'] or '-'}")
            print("  Distribuição             :")
            if item["tier_distribution"]:
                for tier, count in item["tier_distribution"].items():
                    print(f"    - {tier:<12}: {count}")
            else:
                print("    - sem dados individuais")

        print()
        print("=" * 88)
        print("ARQUIVOS GERADOS")
        print("=" * 88)
        print(JSON_OUTPUT.relative_to(ROOT))
        print(CSV_OUTPUT.relative_to(ROOT))
        print(SUMMARY_OUTPUT.relative_to(ROOT))
        print(CHECKPOINT_OUTPUT.relative_to(ROOT))
        print()
        print("IMPORTANTE")
        print("Os ranks acima são atuais no momento da consulta.")
        print("Não trate esses ranks como rank_at_collection ou rank_at_match históricos.")
        print()
        print("AUDITORIA CONCLUÍDA")
        print("Envie desde 'DISTRIBUIÇÃO DE ELOS POR BENCHMARK' até o final.")

    def _write_empty_summary(self, files_report: list[dict[str, Any]]) -> None:
        summary = self._build_summary([], files_report)
        SUMMARY_OUTPUT.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Resumo salvo em: {SUMMARY_OUTPUT.relative_to(ROOT)}")

    def _load_checkpoint(self) -> dict[str, Any]:
        if not CHECKPOINT_OUTPUT.exists():
            return {"players": {}}
        try:
            data = json.loads(CHECKPOINT_OUTPUT.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"players": {}}
        except (OSError, json.JSONDecodeError):
            return {"players": {}}

    def _save_checkpoint_result(
        self,
        identity: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        self.checkpoint.setdefault("players", {})[
            self._checkpoint_key(identity)
        ] = {
            "completed": True,
            "result": result,
        }
        CHECKPOINT_OUTPUT.write_text(
            json.dumps(self.checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _checkpoint_key(identity: dict[str, Any]) -> str:
        return "|".join(
            [
                str(identity.get("benchmark_id") or ""),
                str(identity.get("puuid") or ""),
                str(identity.get("game_name") or "").lower(),
                str(identity.get("tag_line") or "").lower(),
            ]
        )

    @staticmethod
    def _benchmark_from_payload(path: Path, data: Any) -> str:
        if isinstance(data, dict):
            explicit = data.get("benchmark_id") or data.get("id")
            if isinstance(explicit, str) and explicit in KNOWN_BENCHMARKS:
                return explicit
        return BenchmarkRankAudit._benchmark_from_file(path)

    @staticmethod
    def _benchmark_from_file(path: Path) -> str:
        stem = path.stem.lower()
        if stem in CATALOG_TO_BENCHMARK:
            return CATALOG_TO_BENCHMARK[stem]
        for benchmark_id in KNOWN_BENCHMARKS:
            if stem == benchmark_id or stem.startswith(benchmark_id + "_"):
                return benchmark_id
        if "challenger" in stem:
            return "challenger_br"
        return stem

    @staticmethod
    def _first_text(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().removeprefix("#")
        return None

    @staticmethod
    def _has_real_identity(identity: dict[str, Any]) -> bool:
        return bool(
            identity.get("puuid")
            or (identity.get("game_name") and identity.get("tag_line"))
        )

    @staticmethod
    def _deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for item in items:
            key = (
                item.get("benchmark_id"),
                item.get("puuid") or "",
                (item.get("game_name") or "").lower(),
                (item.get("tag_line") or "").lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    @staticmethod
    def _identity_label(identity: dict[str, Any]) -> str:
        if identity.get("game_name") and identity.get("tag_line"):
            return f"{identity['game_name']}#{identity['tag_line']}"
        puuid = str(identity.get("puuid") or "")
        return f"PUUID {puuid[:12]}..." if puuid else "identidade desconhecida"

    @staticmethod
    def _upper(entry: dict[str, Any] | None, key: str) -> str | None:
        if not isinstance(entry, dict):
            return None
        value = entry.get(key)
        return value.strip().upper() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _integer(entry: dict[str, Any] | None, key: str) -> int | None:
        if not isinstance(entry, dict):
            return None
        value = entry.get(key)
        return value if isinstance(value, int) else None

    @staticmethod
    def _min_tier(counts: Counter) -> str | None:
        order = [
            "IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD",
            "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER",
        ]
        present = [tier for tier in order if counts.get(tier)]
        return present[0] if present else None

    @staticmethod
    def _max_tier(counts: Counter) -> str | None:
        order = [
            "IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD",
            "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER",
        ]
        present = [tier for tier in order if counts.get(tier)]
        return present[-1] if present else None


if __name__ == "__main__":
    BenchmarkRankAudit().run()
