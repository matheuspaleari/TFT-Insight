from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.action_signal import ActionSignalEngine
from src.contextual_recommendation import (
    ContextualRecommendationEngine,
)
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

# V1 diagnóstico usa o contexto já validado no projeto atual.
competitive = {
    "group_label": "Avançado BR",
    "spectrum_band": "Entrada",
}

fusion = {
    "problem_observed": (
        "Leveling é a principal oportunidade de treino"
    ),
    "training_focus": "Planejar o próximo nível",
    "strength_to_preserve": "Economia",
}

recommendation = ContextualRecommendationEngine.build(
    action_signals=actions,
    competitive_context=competitive,
    coach_fusion=fusion,
    active_skill_label="Leveling",
    mission_title="Planejar o próximo nível",
)

print()
print("=" * 96)
print("CONTEXTUAL RECOMMENDATION V1")
print("=" * 96)
print(f"Jogador              : {game}#{tag}")
print(f"Partida              : {target.match_id}")
print("Grupo competitivo    : Avançado BR")
print("Faixa                : Entrada")
print("Skill em foco        : Leveling")
print("Missão               : Planejar o próximo nível")

print()
print("RECOMENDAÇÃO PRINCIPAL")
print("-" * 96)
print(recommendation.title)
print(recommendation.recommendation)

print()
print("POR QUE AGORA")
print("-" * 96)
print(recommendation.why_now)

print()
print("CONTEXTO COMPETITIVO")
print("-" * 96)
print(recommendation.competitive_context)

print()
print("CONTEXTO DE TREINO")
print("-" * 96)
print(recommendation.training_context)

if recommendation.preserve:
    print()
    print("PONTO FORTE A PRESERVAR")
    print("-" * 96)
    print(recommendation.preserve)

if recommendation.secondary_actions:
    print()
    print("AÇÕES DE APOIO")
    print("-" * 96)
    for item in recommendation.secondary_actions:
        print(f"- {item}")

print()
print("PROTEÇÕES")
print("-" * 96)
print(f"changes_learning_priority : {recommendation.changes_learning_priority}")
print(f"changes_mission           : {recommendation.changes_mission}")
print(f"changes_difficulty        : {recommendation.changes_difficulty}")
print(f"changes_evidence_class    : {recommendation.changes_evidence_class}")
print(f"counts_as_mission_evidence: {recommendation.counts_as_mission_evidence}")
print(f"predicts_rank_up          : {recommendation.predicts_rank_up}")

print()
print("=" * 96)
print("DIAGNÓSTICO CONCLUÍDO")
print("Envie desde 'CONTEXTUAL RECOMMENDATION V1' até o final.")
print("=" * 96)
