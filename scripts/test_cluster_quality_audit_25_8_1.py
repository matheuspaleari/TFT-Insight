
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decision_engine.models import CompositionSnapshot
from src.composition_intelligence_v2.services.cluster_quality_audit_service import (
    ClusterQualityAuditService,
)


def snap(
    mid,
    *,
    carry,
    traits,
    units,
    support="",
):
    return CompositionSnapshot(
        match_id=mid,
        placement=4,
        carry_character_id=carry,
        tank_character_id="Tank",
        support_character_id=support,
        trait_names=tuple(traits),
        unit_ids=tuple(units),
        composition_key=mid,
    )


snapshots = (
    snap(
        "A1",
        carry="CarryA",
        traits=("TraitA", "TraitB"),
        units=("CarryA", "Tank", "U1", "U2", "Flex1"),
        support="SupportA",
    ),
    snap(
        "A2",
        carry="CarryA",
        traits=("TraitA", "TraitB"),
        units=("CarryA", "Tank", "U1", "U2", "Flex2"),
    ),
    snap(
        "B1",
        carry="CarryB",
        traits=("TraitC", "TraitD"),
        units=("CarryB", "TankB", "V1", "V2", "V3"),
    ),
)

report = ClusterQualityAuditService.analyze(
    snapshots
)

sim55 = next(
    item
    for item in report.threshold_simulations
    if item.threshold == 55.0
)

checks = [
    ("3 snapshots", report.snapshot_count == 3),
    ("3 pares", report.pair_count == 3),
    ("Threshold atual 55", report.current_threshold == 55.0),
    ("Tem simulações 45-65", len(report.threshold_simulations) == 5),
    ("A1/A2 agrupam em 55", sim55.cluster_count == 2),
    ("Support rate auditado", report.support_identification_rate > 0),
    ("Near-boundary é tuple", isinstance(report.near_boundary_pairs, tuple)),
    ("to_dict funciona", isinstance(report.to_dict(), dict)),
]

print("=" * 96)
print("#25.8.1 - CLUSTER QUALITY AUDIT")
print("=" * 96)

passed = 0
for i, (name, ok) in enumerate(checks, 1):
    passed += int(ok)
    print()
    print(f"[{i}] {name}")
    print(f"Status  : {'OK' if ok else 'ERRO'}")

print()
print("=" * 96)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed == len(checks):
    print("#25.8.1 CLUSTER QUALITY AUDIT: VALIDADO")
else:
    raise SystemExit(1)
