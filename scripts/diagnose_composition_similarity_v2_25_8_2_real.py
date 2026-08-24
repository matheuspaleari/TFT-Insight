
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer
from src.decision_engine import (
    CompositionHistoryAnalyzer,
    ContestHistoryAnalyzer,
)
from src.integration_engine.services.item_classification_provider import (
    ItemClassificationProvider,
)
from src.composition_intelligence_v2.services.composition_similarity_ab_audit_service import (
    CompositionSimilarityABAuditService,
)


def load_valid_matches(
    *,
    client,
    puuid,
    requested,
):
    candidate_count = min(
        max(
            requested * 2,
            requested + 10,
        ),
        100,
    )

    ids = client.get_match_ids(
        puuid=puuid,
        count=candidate_count,
    )

    matches = []
    skipped = []

    for match_id in ids:
        if len(
            matches
        ) >= requested:
            break

        try:
            payload = client.get_match_details(
                match_id=match_id
            )
            match = MatchTransformer.transform(
                match_data=payload,
                puuid=puuid,
            )
        except (
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            skipped.append(
                (
                    match_id,
                    str(
                        error
                    ),
                )
            )
            print(
                f"[SKIP] "
                f"{match_id} · {error}"
            )
            continue

        matches.append(
            match
        )

        print(
            f"[{len(matches):02d}/{requested}] "
            f"{match.match_id} · "
            f"{match.placement}º"
        )

    return (
        matches,
        skipped,
    )


def print_change(
    item,
) -> None:
    print(
        f"{item.first_match_id} × "
        f"{item.second_match_id}"
    )
    print(
        f"  Carry              : "
        f"{item.first_carry or '-'} × "
        f"{item.second_carry or '-'}"
    )
    print(
        f"  V1                 : "
        f"{item.v1_score:.2f} "
        f"({'MERGE' if item.v1_merge else 'SPLIT'})"
    )
    print(
        f"  V2                 : "
        f"{item.v2_score:.2f} "
        f"({'MERGE' if item.v2_merge else 'SPLIT'})"
    )
    print(
        "  Traits compartilh.: "
        + (
            ", ".join(
                item.shared_traits
            )
            or "-"
        )
    )
    print(
        "  Units compartilh. : "
        + (
            ", ".join(
                item.shared_units
            )
            or "-"
        )
    )
    print(
        f"  Motivo V2          : "
        f"{item.v2_reason}"
    )


def main() -> None:
    game = input(
        "Riot ID (Game Name): "
    ).strip()
    tag = input(
        "Tag: "
    ).strip()
    requested = int(
        input(
            "Partidas válidas [30]: "
        ).strip()
        or "30"
    )

    client = RiotClient()

    puuid = client.get_account(
        game_name=game,
        tag_line=tag,
    )["puuid"]

    matches, skipped = load_valid_matches(
        client=client,
        puuid=puuid,
        requested=requested,
    )

    if len(
        matches
    ) < 3:
        raise RuntimeError(
            "Amostra insuficiente."
        )

    classifications = (
        ItemClassificationProvider(
            project_root=ROOT
        ).get()
    )

    contest = (
        ContestHistoryAnalyzer.analyze(
            matches
        )
    )

    history = (
        CompositionHistoryAnalyzer.analyze(
            matches,
            contest_history=contest,
            item_classifications=classifications,
        )
    )

    report = (
        CompositionSimilarityABAuditService.analyze(
            history.snapshots,
            threshold=55.0,
        )
    )

    print()
    print("=" * 112)
    print(
        "#25.8.2 COMPOSITION SIMILARITY V2 - A/B REAL"
    )
    print("=" * 112)

    print(
        f"Jogador                  : "
        f"{game}#{tag}"
    )
    print(
        f"Snapshots                : "
        f"{report.snapshot_count}"
    )
    print(
        f"Partidas ignoradas       : "
        f"{len(skipped)}"
    )
    print(
        f"Threshold                : "
        f"{report.threshold:.2f}"
    )

    print()
    print(
        "RESUMO A/B"
    )
    print(
        "-" * 112
    )
    print(
        "Engine | Clusters | Singletons | Maior cluster | Tamanho médio"
    )

    for summary in (
        report.v1,
        report.v2,
    ):
        print(
            f"{summary.engine:<6} | "
            f"{summary.cluster_count:8d} | "
            f"{summary.singleton_count:10d} | "
            f"{summary.largest_cluster_size:13d} | "
            f"{summary.average_cluster_size:12.2f}"
        )

    print()
    print(
        "CONSISTÊNCIA DE CARRY"
    )
    print(
        "-" * 112
    )
    print(
        f"Pares com mesmo carry    : "
        f"{report.same_carry_pairs}"
    )
    print(
        f"Merge V1                 : "
        f"{report.same_carry_merged_v1}"
    )
    print(
        f"Merge V2                 : "
        f"{report.same_carry_merged_v2}"
    )
    print(
        f"Support usado pela V2    : "
        f"{report.support_used_by_v2}"
    )

    print()
    print(
        "V1 JUNTAVA / V2 SEPARA"
    )
    print(
        "-" * 112
    )

    if report.old_merge_new_split:
        for item in (
            report.old_merge_new_split[
                :20
            ]
        ):
            print()
            print_change(
                item
            )
    else:
        print(
            "Nenhum caso."
        )

    print()
    print(
        "V1 SEPARAVA / V2 JUNTA"
    )
    print(
        "-" * 112
    )

    if report.old_split_new_merge:
        for item in (
            report.old_split_new_merge[
                :20
            ]
        ):
            print()
            print_change(
                item
            )
    else:
        print(
            "Nenhum caso."
        )

    print()
    print(
        "NOTAS"
    )
    print(
        "-" * 112
    )

    for item in report.notes:
        print(
            "-",
            item,
        )

    output_dir = (
        ROOT
        / "data"
        / "diagnostics"
        / "composition_similarity_v2"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / "composition_similarity_ab_report.json"
    )

    output_path.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "ARQUIVO"
    )
    print(
        "-" * 112
    )
    print(
        output_path
    )

    print()
    print("=" * 112)
    print(
        "DIAGNÓSTICO CONCLUÍDO"
    )
    print(
        "Envie desde "
        "'#25.8.2 COMPOSITION SIMILARITY V2 - A/B REAL' "
        "até o final."
    )
    print("=" * 112)


if __name__ == "__main__":
    main()
