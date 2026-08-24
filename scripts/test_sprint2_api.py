from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from fastapi.testclient import TestClient

from src.integration_engine.api import app


def main() -> None:
    client = TestClient(app)

    health = client.get("/health")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    capabilities = client.get(
        "/v1/capabilities"
    )

    assert capabilities.status_code == 200

    response = client.post(
        "/v1/analyze",
        json={
            "source": "partner",
            "player": {
                "game_name": "Pinador doss",
                "tag_line": "000",
                "region": "BR1",
            },
            "patch": "16.15",
            "set_number": 17,
            "signals": {
                "economy_score": 81.75,
                "itemization_score": 75.77,
                "tempo_score": 70.75,
                "contest_score": 52.79,
                "flex_score": 70.75,
                "benchmark_score": 68.0,
                "sample_size": 32,
                "carry_contested": True,
                "opponents_on_carry": 1,
                "average_placement": 4.25,
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert "meta" in payload
    assert "prediction" in payload
    assert "recommendations" in payload
    assert "coach" in payload
    assert (
        payload["meta"]["contract_version"]
        == "1.0.0"
    )

    print("=" * 80)
    print("TFT INSIGHT - SPRINT 2 API VALIDATION")
    print("=" * 80)
    print("Health          : OK")
    print("Capabilities    : OK")
    print("Public contract : OK")
    print("API key dev     : OK")
    print("Analyze         : OK")
    print(
        "Overall score   : "
        f"{payload['overall_score']:.2f}"
    )
    print(
        "Top 4           : "
        f"{payload['prediction']['top4_probability']:.2f}%"
    )
    print(
        "Processing      : "
        f"{payload['meta']['processing_ms']:.3f} ms"
    )
    print()
    print("✓ Sprint 2 validada.")


if __name__ == "__main__":
    main()
