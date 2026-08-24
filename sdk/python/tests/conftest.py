from datetime import datetime, timezone

import pytest


@pytest.fixture
def analyze_payload() -> dict:
    return {
        "meta": {
            "request_id": "req-1",
            "api_version": "1.0.0",
            "contract_version": "1.0.0",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "processing_ms": 0.2,
        },
        "overall_score": 70.02,
        "classification": "Boa",
        "prediction": {
            "top1_probability": 14.2,
            "top4_probability": 72.64,
            "bot4_probability": 27.36,
            "expected_placement": 3.9,
            "risk": "Médio",
            "confidence": 81.28,
        },
        "feature_importance": [],
        "recommendations": [],
        "coach": {
            "headline": "Prioridade principal: Contestação",
            "summary": "Monitore o carry.",
            "pregame_attention": "Evite fechar cedo.",
            "win_condition": "Complete carry e tank.",
        },
        "evidence": [],
        "limitations": [],
    }


@pytest.fixture
def integrated_payload(
    analyze_payload: dict,
) -> dict:
    return {
        "analysis": analyze_payload,
        "cache": {
            "match_ids_received": 20,
            "cached_matches_used": 20,
            "new_matches_downloaded": 0,
            "transformed_matches": 20,
            "failed_matches": 0,
        },
        "learning": {
            "enabled": True,
            "inserted": 0,
            "reused": 20,
            "observations_written": 0,
        },
        "player_puuid": "puuid-test",
        "matches_analyzed": 20,
        "patch": "16.15",
        "set_number": 17,
    }
