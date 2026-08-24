from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.action_signal import ActionSignalEngine
from src.post_match import (
    PersonalBaselineService,
    PostMatchAnalysisService,
)
from src.post_match.services.historical_match_context_service import (
    HistoricalMatchContextService,
)
from src.post_match.services.historical_context_interpretation_service import (
    HistoricalContextInterpretationService,
)
from src.post_match.services.post_match_interpretation_service import (
    PostMatchInterpretationService,
)
from src.post_match.services.post_match_report_service import (
    PostMatchReportService,
)
from src.decision_engine import ContestAnalyzer
from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer


game = input("Riot ID (Game Name): ").strip()
tag = input("Tag: ").strip()

client = RiotClient()
puuid = client.get_account(
    game_name=game,
    tag_line=tag,
)["puuid"]

ids = client.get_match_ids(
    puuid=puuid,
    count=11,
)

matches = []
for i, match_id in enumerate(ids, 1):
    payload = client.get_match_details(
        match_id=match_id
    )
    match = MatchTransformer.transform(
        match_data=payload,
        puuid=puuid,
    )
    matches.append(match)
    print(
        f"[{i:02d}/11] {match.match_id} · "
        f"{match.placement}º · lvl {match.level} · "
        f"gold {match.gold_left}"
    )

target = matches[0]
history = matches[1:]

training = {
    "primary_skill_id": "leveling",
    "primary_skill_label": "Leveling",
    "mission_title": "Planejar o próximo nível",
    "objective": (
        "Antes de gastar ouro, defina qual será seu próximo "
        "momento de subida de nível."
    ),
}

analysis = PostMatchAnalysisService.analyze(
    match=target,
    training=training,
    contest_report=ContestAnalyzer.analyze(target),
)

baseline = PersonalBaselineService.compare(
    target_match=target,
    prior_matches=history,
    requested_history_size=10,
)

post_interpretation = PostMatchInterpretationService.interpret(
    analysis=analysis,
    baseline=baseline,
)

historical = HistoricalMatchContextService.analyze(
    target_match=target,
    prior_matches=history,
    baseline_report=baseline,
)

historical_interpretation = HistoricalContextInterpretationService.interpret(
    historical_context=historical,
    active_skill_id="leveling",
    active_skill_label="Leveling",
)

post_report = PostMatchReportService.build(
    analysis=analysis,
    baseline=baseline,
    post_match_interpretation=post_interpretation,
    historical_context=historical,
    historical_interpretation=historical_interpretation,
)

actions = ActionSignalEngine.build(
    post_match_report=post_report,
    post_match_analysis=analysis,
    historical_context=historical,
    active_skill_id="leveling",
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
)

print()
print("=" * 96)
print("ACTION SIGNAL ENGINE V1")
print("=" * 96)
print(f"Jogador              : {game}#{tag}")
print(f"Partida              : {target.match_id}")
print("Skill em foco        : Leveling")
print("Missão               : Planejar o próximo nível")

print()
print("PRIORIDADE PRINCIPAL")
print("-" * 96)
print(actions.primary.title)
print(actions.primary.action)
print()
print("Por quê:")
print(actions.primary.reason)

if actions.secondary:
    print()
    print("SINAIS DE APOIO")
    print("-" * 96)
    for item in actions.secondary:
        print()
        print(item.title)
        print(item.action)
        print(f"Motivo: {item.reason}")

if actions.watch:
    print()
    print("PARA ACOMPANHAR")
    print("-" * 96)
    for item in actions.watch:
        print()
        print(item.title)
        print(item.action)
        print(f"Motivo: {item.reason}")

print()
print("PROTEÇÕES")
print("-" * 96)
print(f"changes_learning_priority : {actions.changes_learning_priority}")
print(f"changes_mission           : {actions.changes_mission}")
print(f"changes_difficulty        : {actions.changes_difficulty}")
print(f"changes_evidence_class    : {actions.changes_evidence_class}")
print(f"counts_as_mission_evidence: {actions.counts_as_mission_evidence}")
print(f"predicts_rank_up          : {actions.predicts_rank_up}")

print()
print("=" * 96)
print("DIAGNÓSTICO CONCLUÍDO")
print("Envie desde 'ACTION SIGNAL ENGINE V1' até o final.")
print("=" * 96)
