from copy import deepcopy
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.coaching_engine import ChallengerBenchmarkEngine
from src.transformers.match_transformer import MatchTransformer


CACHE = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "challenger"
    / "matches"
)

OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "benchmarks"
    / "challenger_metrics.json"
)


def sanitize_match_payload(
    payload: dict,
) -> tuple[dict, str] | None:
    """
    Remove participantes duplicados por PUUID antes da transformação.

    Alguns arquivos do cache podem conter o mesmo participante repetido
    em info.participants ou metadata.participants. O modelo Match rejeita
    corretamente PUUIDs duplicados, então normalizamos o JSON de entrada.
    """

    sanitized = deepcopy(payload)

    metadata = sanitized.get("metadata")
    info = sanitized.get("info")

    if not isinstance(metadata, dict):
        return None

    if not isinstance(info, dict):
        return None

    raw_participants = info.get("participants")

    if not isinstance(raw_participants, list):
        return None

    unique_participants = []
    seen_puuids = set()

    for participant in raw_participants:
        if not isinstance(participant, dict):
            continue

        puuid = str(
            participant.get("puuid", "")
            or ""
        ).strip()

        if not puuid:
            continue

        if puuid in seen_puuids:
            continue

        seen_puuids.add(puuid)
        unique_participants.append(participant)

    if not unique_participants:
        return None

    info["participants"] = unique_participants

    # Mantém metadata.participants consistente com info.participants.
    metadata["participants"] = [
        participant["puuid"]
        for participant in unique_participants
    ]

    analyzed_puuid = unique_participants[0]["puuid"]

    return sanitized, analyzed_puuid


def main() -> None:
    if not CACHE.exists():
        raise RuntimeError(
            "Cache Challenger não encontrado em: "
            f"{CACHE}"
        )

    matches = []

    total_files = 0
    sanitized_files = 0
    skipped_files = 0

    for path in sorted(CACHE.glob("*.json")):
        total_files += 1

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )

            if not isinstance(payload, dict):
                skipped_files += 1
                continue

            original_count = len(
                payload.get(
                    "info",
                    {},
                ).get(
                    "participants",
                    [],
                )
            )

            sanitized_result = sanitize_match_payload(
                payload
            )

            if sanitized_result is None:
                skipped_files += 1
                print(
                    f"Ignorada: {path.name} "
                    "(participantes inválidos)"
                )
                continue

            sanitized_payload, puuid = sanitized_result

            sanitized_count = len(
                sanitized_payload[
                    "info"
                ][
                    "participants"
                ]
            )

            if sanitized_count < original_count:
                sanitized_files += 1
                print(
                    f"Normalizada: {path.name} "
                    f"({original_count} → "
                    f"{sanitized_count} participantes)"
                )

            match = MatchTransformer.transform(
                match_data=sanitized_payload,
                puuid=puuid,
            )

            matches.append(match)

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            skipped_files += 1
            print(
                f"Ignorada: {path.name} "
                f"({error})"
            )

    if not matches:
        raise RuntimeError(
            "Nenhuma partida Challenger válida "
            "foi encontrada no cache."
        )

    metrics = ChallengerBenchmarkEngine.build_metrics(
        matches=matches
    )

    metrics["cache_files"] = total_files
    metrics["valid_matches"] = len(matches)
    metrics["sanitized_files"] = sanitized_files
    metrics["skipped_files"] = skipped_files

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            metrics,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print(
        "TFT INSIGHT - CHALLENGER BENCHMARK"
    )
    print("=" * 80)

    for key, value in metrics.items():
        print(
            f"{key:<24}: {value}"
        )

    print()
    print(
        f"✓ Métricas salvas em: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
