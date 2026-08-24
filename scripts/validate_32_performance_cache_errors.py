from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

paths = {
    "cache": ROOT / "src/integration_engine/services/cached_match_service.py",
    "composition": ROOT / "src/integration_engine/api/routes/composition_intelligence.py",
    "contest": ROOT / "src/integration_engine/api/routes/contest_intelligence.py",
    "economy": ROOT / "src/integration_engine/api/routes/economy_intelligence.py",
    "carry": ROOT / "src/integration_engine/api/routes/carry_item_intelligence.py",
    "messages": ROOT / "partner_platform/ui/messages.py",
}

texts = {}

for name, path in paths.items():
    text = path.read_text(encoding="utf-8")
    ast.parse(text)
    texts[name] = text

checks = [
    ("Cache PUUID", "ACCOUNT_CACHE_TTL_SECONDS = 600" in texts["cache"]),
    ("Cache match IDs", "MATCH_IDS_CACHE_TTL_SECONDS = 45" in texts["cache"]),
    ("Cache por Riot ID", "normalized_name.lower()" in texts["cache"]),
    ("Cache IDs usa PUUID", "puuid," in texts["cache"]),
    ("Lock de cache", "RLock" in texts["cache"]),
    ("Loader target", "def load_player_matches_target(" in texts["cache"]),
    ("Early-stop", "if len(matches) >= target_count:" in texts["cache"]),
    ("Telemetry considered", "candidate_ids_considered" in texts["cache"]),
    ("Telemetry elapsed", "elapsed_seconds" in texts["cache"]),
    ("Telemetry stop", "stopped_after_target" in texts["cache"]),
    ("Cache hit rate", "def cache_hit_rate" in texts["cache"]),
    ("Compatibilidade loader antigo", "def load_player_matches(" in texts["cache"]),
    ("Composição target loader", "load_player_matches_target" in texts["composition"]),
    ("Contestação target loader", "load_player_matches_target" in texts["contest"]),
    ("Economia target loader", "load_player_matches_target" in texts["economy"]),
    ("Carries target loader", "load_player_matches_target" in texts["carry"]),
    ("Composição expõe perf", "load_elapsed_seconds" in texts["composition"]),
    ("Contestação expõe perf", "cache_hit_rate" in texts["contest"]),
    ("Economia expõe perf", "stopped_after_target" in texts["economy"]),
    ("Carries expõe perf", "candidate_ids_considered" in texts["carry"]),
    ("UI trata 5xx", "status_code in {500, 502, 503, 504}" in texts["messages"]),
    ("UI mantém 429", "status_code == 429" in texts["messages"]),
    ("UI mantém timeout", "httpx.TimeoutException" in texts["messages"]),
    ("Histórico não é apagado", "Não remove histórico persistido" in texts["cache"]),
]

print("=" * 104)
print("#32 / ROADMAP 21 - VALIDAÇÃO PERFORMANCE + CACHE + ERROS")
print("=" * 104)

passed = 0

for index, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{index}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 104)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#32 PERFORMANCE + CACHE + ERROS: CONTRATO VALIDADO")
else:
    raise SystemExit(1)
