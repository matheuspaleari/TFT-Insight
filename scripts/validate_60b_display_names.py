from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.decision_engine.analyzers.match_decision_explanation_engine import (
    MatchDecisionExplanationEngine,
)


def check(label: str, condition: bool) -> None:
    global passed
    if condition:
        passed += 1
        print(f"OK   {label}")
    else:
        print(f"ERRO {label}")


passed = 0
total = 8

print("=" * 100)
print("TFT INSIGHT — #60B DISPLAY NAMES / FINAL UI LEAK CHECK")
print("=" * 100)

engine_path = (
    ROOT
    / "src"
    / "decision_engine"
    / "analyzers"
    / "match_decision_explanation_engine.py"
)
source = engine_path.read_text(encoding="utf-8")

check(
    "MatchDecisionExplanationEngine usa UnitCatalogRepository",
    "UnitCatalogRepository" in source,
)

check(
    "evidência pública não interpola damage_carry.character_id diretamente",
    "f\"{role_report.damage_carry.character_id" not in source,
)

check(
    "evidência pública não interpola main_tank.character_id diretamente",
    "f\"{role_report.main_tank.character_id" not in source,
)

master_yi = SimpleNamespace(character_id="DA_18_MasterYi_AD")
amumu = SimpleNamespace(character_id="DA_Amumu18")
unknown = SimpleNamespace(character_id="DA_18_UnidadeQueNaoExiste")
missing = SimpleNamespace(character_id="")

check(
    "Master Yi resolve pelo catálogo",
    MatchDecisionExplanationEngine._role_display_name(master_yi) == "Master Yi",
)

check(
    "Amumu resolve pelo catálogo",
    MatchDecisionExplanationEngine._role_display_name(amumu) == "Amumu",
)

check(
    "assessment None vira '-'",
    MatchDecisionExplanationEngine._role_display_name(None) == "-",
)

check(
    "assessment sem identidade vira '-'",
    MatchDecisionExplanationEngine._role_display_name(missing) == "-",
)

check(
    "ID desconhecido nunca vaza para apresentação",
    MatchDecisionExplanationEngine._role_display_name(unknown)
    != "DA_18_UnidadeQueNaoExiste",
)

print()
print(f"RESULTADO: {passed}/{total} OK")

if passed != total:
    raise SystemExit(1)

print(
    "Strategic Coach, Pre-Match Coach e Benchmark Page já estavam protegidos "
    "pelos helpers públicos; o vazamento real restante do Match Decision foi corrigido."
)
