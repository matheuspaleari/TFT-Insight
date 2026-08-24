
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decision_engine.models import CompositionSnapshot
from src.composition_intelligence_v2.services.composition_similarity_analyzer_v2 import (
    CompositionSimilarityAnalyzerV2,
)
from src.composition_intelligence_v2.services.composition_similarity_ab_audit_service import (
    CompositionSimilarityABAuditService,
)


def snap(
    mid,
    *,
    carry,
    tank,
    traits,
    units,
    support="",
):
    return CompositionSnapshot(
        match_id=mid,
        placement=4,
        carry_character_id=carry,
        tank_character_id=tank,
        support_character_id=support,
        trait_names=tuple(traits),
        unit_ids=tuple(units),
        composition_key=mid,
    )


trait_only_a = snap(
    "TRAIT_A",
    carry="Jhin",
    tank="Tank1",
    traits=("DarkStar",),
    units=("Jhin","Nunu","A","B","C"),
)

trait_only_b = snap(
    "TRAIT_B",
    carry="Bard",
    tank="Tank2",
    traits=("DarkStar",),
    units=("Bard","Nunu","X","Y","Z"),
)

same_carry_a = snap(
    "KINDRED_A",
    carry="Kindred",
    tank="Maokai",
    traits=("DRX","TraitX"),
    units=("Kindred","Maokai","U1","U2","U3"),
)

same_carry_b = snap(
    "KINDRED_B",
    carry="Kindred",
    tank="Maokai",
    traits=("DRX","TraitY"),
    units=("Kindred","Maokai","U4","U5","U6"),
)

structural_a = snap(
    "STRUCT_A",
    carry="CarryA",
    tank="TankA",
    traits=("Trait1","Trait2"),
    units=("CarryA","TankA","U1","U2","U3"),
)

structural_b = snap(
    "STRUCT_B",
    carry="CarryB",
    tank="TankB",
    traits=("Trait1","Trait2"),
    units=("CarryB","TankA","U1","U2","U3"),
)

trait_only = CompositionSimilarityAnalyzerV2.compare(
    trait_only_a,
    trait_only_b,
)

same_carry = CompositionSimilarityAnalyzerV2.compare(
    same_carry_a,
    same_carry_b,
)

structural = CompositionSimilarityAnalyzerV2.compare(
    structural_a,
    structural_b,
)

report = CompositionSimilarityABAuditService.analyze(
    (
        trait_only_a,
        trait_only_b,
        same_carry_a,
        same_carry_b,
        structural_a,
        structural_b,
    )
)

checks = [
    (
        "Trait-only com carry diferente não merge",
        trait_only.score < 55.0,
    ),
    (
        "Same carry recebe âncora forte",
        same_carry.score >= 55.0,
    ),
    (
        "Variante estrutural pode merge",
        structural.score >= 55.0,
    ),
    (
        "Support não entra no V2",
        report.support_used_by_v2 is False,
    ),
    (
        "A/B produz resumo V1",
        report.v1.cluster_count >= 1,
    ),
    (
        "A/B produz resumo V2",
        report.v2.cluster_count >= 1,
    ),
    (
        "Conta pares mesmo carry",
        report.same_carry_pairs >= 1,
    ),
    (
        "to_dict funciona",
        isinstance(report.to_dict(), dict),
    ),
]

print("=" * 100)
print("#25.8.2 - COMPOSITION SIMILARITY V2 + A/B AUDIT")
print("=" * 100)

passed = 0

for index, (name, ok) in enumerate(
    checks,
    1,
):
    passed += int(ok)
    print()
    print(
        f"[{index}] {name}"
    )
    print(
        f"Status  : "
        f"{'OK' if ok else 'ERRO'}"
    )

print()
print("=" * 100)
print(
    f"PASSARAM: "
    f"{passed}/{len(checks)}"
)

if passed == len(checks):
    print(
        "#25.8.2 COMPOSITION SIMILARITY V2: VALIDADO"
    )
else:
    raise SystemExit(1)
