
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.riot_client import RiotClient
from src.transformers.match_transformer import MatchTransformer
from src.decision_engine import CompositionHistoryAnalyzer, ContestHistoryAnalyzer
from src.integration_engine.services.item_classification_provider import (
    ItemClassificationProvider,
)
from src.composition_intelligence_v2.services.cluster_quality_audit_service import (
    ClusterQualityAuditService,
)


def _valid_matches(
    *,
    client,
    puuid: str,
    requested: int,
):
    candidate_count = min(
        max(requested * 2, requested + 10),
        100,
    )
    ids = client.get_match_ids(
        puuid=puuid,
        count=candidate_count,
    )

    matches = []
    skipped = []

    for match_id in ids:
        if len(matches) >= requested:
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
                    str(error),
                )
            )
            print(
                f"[SKIP] {match_id} · {error}"
            )
            continue

        matches.append(match)
        print(
            f"[{len(matches):02d}/{requested}] "
            f"{match.match_id} · {match.placement}º"
        )

    return matches, skipped


def _pair_line(item) -> str:
    return (
        f"{item.first_match_id} × {item.second_match_id} | "
        f"score={item.total_score:5.2f} | "
        f"carry={item.carry_score:5.1f} | "
        f"traits={item.trait_score:5.1f} | "
        f"units={item.unit_score:5.1f} | "
        f"Δ55={item.distance_to_current_threshold:+5.2f}"
    )


def main() -> None:
    game = input(
        "Riot ID (Game Name): "
    ).strip()
    tag = input(
        "Tag: "
    ).strip()
    count = int(
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

    matches, skipped = _valid_matches(
        client=client,
        puuid=puuid,
        requested=count,
    )

    classifications = (
        ItemClassificationProvider(
            project_root=ROOT
        ).get()
    )

    contest = ContestHistoryAnalyzer.analyze(
        matches
    )

    history = CompositionHistoryAnalyzer.analyze(
        matches,
        contest_history=contest,
        item_classifications=classifications,
    )

    audit = ClusterQualityAuditService.analyze(
        history.snapshots
    )

    print()
    print("=" * 108)
    print(
        "#25.8.1 CLUSTER QUALITY AUDIT - REAL"
    )
    print("=" * 108)

    print(
        f"Jogador                  : {game}#{tag}"
    )
    print(
        f"Snapshots                : {audit.snapshot_count}"
    )
    print(
        f"Partidas ignoradas       : {len(skipped)}"
    )
    print(
        f"Threshold atual          : {audit.current_threshold:.2f}"
    )
    print(
        f"Pares avaliados          : {audit.pair_count}"
    )
    print(
        f"Similaridade mínima      : {audit.minimum_similarity:.2f}"
    )
    print(
        f"Similaridade mediana     : {audit.median_similarity:.2f}"
    )
    print(
        f"Similaridade máxima      : {audit.maximum_similarity:.2f}"
    )

    print()
    print(
        "SENSIBILIDADE AO THRESHOLD"
    )
    print(
        "-" * 108
    )
    print(
        "Threshold | Clusters | Singletons | Maior cluster | Tamanho médio"
    )

    for item in audit.threshold_simulations:
        print(
            f"{item.threshold:9.1f} | "
            f"{item.cluster_count:8d} | "
            f"{item.singleton_count:10d} | "
            f"{item.largest_cluster_size:13d} | "
            f"{item.average_cluster_size:12.2f}"
        )

    print()
    print(
        "PARES PRÓXIMOS AO THRESHOLD ATUAL (±7.5)"
    )
    print(
        "-" * 108
    )

    if audit.near_boundary_pairs:
        for item in audit.near_boundary_pairs[:25]:
            print(
                _pair_line(item)
            )
            print(
                f"  carry: {item.first_carry or '-'} × "
                f"{item.second_carry or '-'}"
            )
            print(
                "  traits compartilhadas: "
                + (
                    ", ".join(item.shared_traits)
                    or "-"
                )
            )
            print(
                "  units compartilhadas : "
                + (
                    ", ".join(item.shared_units)
                    or "-"
                )
            )
    else:
        print(
            "Nenhum par ficou próximo da fronteira."
        )

    print()
    print(
        "MAIORES SCORES AINDA ABAIXO DE 55"
    )
    print(
        "-" * 108
    )
    for item in audit.highest_separated_pairs:
        print(
            _pair_line(item)
        )

    print()
    print(
        "MENORES SCORES JÁ ACIMA/IGUAL A 55"
    )
    print(
        "-" * 108
    )
    for item in audit.lowest_merged_pairs:
        print(
            _pair_line(item)
        )

    print()
    print(
        "AUDITORIA DE SUPPORT"
    )
    print(
        "-" * 108
    )
    print(
        f"Support identificado     : "
        f"{audit.support_identified_count}"
    )
    print(
        f"Support ausente          : "
        f"{audit.support_missing_count}"
    )
    print(
        f"Taxa de identificação    : "
        f"{audit.support_identification_rate:.2f}%"
    )

    print()
    print(
        "LEITURA DE AMOSTRA / CONFIANÇA"
    )
    print(
        "-" * 108
    )
    print(
        "A partir daqui vamos separar dois conceitos:"
    )
    print(
        "- Elegível para comparação: >= 3 partidas."
    )
    print(
        "- Confiança estatística: continua usando o Confidence Engine."
    )
    print(
        "Portanto, 3 partidas podem ser elegíveis para comparação "
        "e ainda ter confiança estatística Baixa."
    )

    print()
    print(
        "NOTAS"
    )
    print(
        "-" * 108
    )
    for note in audit.notes:
        print(
            "-",
            note,
        )

    output_dir = (
        ROOT
        / "data"
        / "diagnostics"
        / "composition_cluster_quality"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        output_dir
        / "cluster_quality_audit.json"
    )
    json_path.write_text(
        json.dumps(
            audit.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    csv_path = (
        output_dir
        / "pair_similarities.csv"
    )
    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "first_match_id",
                "second_match_id",
                "total_score",
                "carry_score",
                "trait_score",
                "unit_score",
                "first_carry",
                "second_carry",
                "shared_traits",
                "shared_units",
                "distance_to_threshold",
                "near_boundary",
            )
        )

        pairs = (
            list(audit.near_boundary_pairs)
            + list(audit.highest_separated_pairs)
            + list(audit.lowest_merged_pairs)
        )

        seen = set()
        for item in pairs:
            key = (
                item.first_match_id,
                item.second_match_id,
            )
            if key in seen:
                continue
            seen.add(key)

            writer.writerow(
                (
                    item.first_match_id,
                    item.second_match_id,
                    item.total_score,
                    item.carry_score,
                    item.trait_score,
                    item.unit_score,
                    item.first_carry,
                    item.second_carry,
                    ";".join(item.shared_traits),
                    ";".join(item.shared_units),
                    item.distance_to_current_threshold,
                    item.near_boundary,
                )
            )

    print()
    print(
        "ARQUIVOS GERADOS"
    )
    print(
        "-" * 108
    )
    print(
        json_path
    )
    print(
        csv_path
    )

    print()
    print("=" * 108)
    print(
        "DIAGNÓSTICO CONCLUÍDO"
    )
    print(
        "Envie desde '#25.8.1 CLUSTER QUALITY AUDIT - REAL' até o final."
    )
    print("=" * 108)


if __name__ == "__main__":
    main()
