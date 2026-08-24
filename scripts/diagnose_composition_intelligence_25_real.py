from __future__ import annotations

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
from src.composition_intelligence_v2 import CompositionIntelligenceV2


def _is_duplicate_puuid_error(error: Exception) -> bool:
    return "PUUIDs duplicados" in str(error)


def main() -> None:
    game = input("Riot ID (Game Name): ").strip()
    tag = input("Tag: ").strip()
    requested_raw = input("Partidas válidas [30]: ").strip()
    requested = int(requested_raw or "30")

    if requested < 1:
        raise ValueError(
            "A quantidade de partidas deve ser maior que zero."
        )

    candidate_count = min(
        max(
            requested * 2,
            requested + 10,
        ),
        100,
    )

    client = RiotClient()
    puuid = client.get_account(
        game_name=game,
        tag_line=tag,
    )["puuid"]

    ids = client.get_match_ids(
        puuid=puuid,
        count=candidate_count,
    )

    matches = []
    skipped = []

    print()
    print(
        f"Buscando até {len(ids)} candidata(s) "
        f"para obter {requested} partida(s) válida(s)..."
    )

    for _, match_id in enumerate(ids, 1):
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
            reason = str(error).strip()

            if _is_duplicate_puuid_error(
                error
            ):
                reason = (
                    "participantes com PUUID duplicado; "
                    "partida incompatível com o modelo analítico atual"
                )

            skipped.append(
                (
                    match_id,
                    reason,
                )
            )

            print(
                f"[SKIP] {match_id} · {reason}"
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

    if len(matches) < requested:
        print()
        print(
            "AVISO: não foi possível obter a quantidade "
            "solicitada de partidas válidas."
        )
        print(
            f"Solicitadas: {requested}"
        )
        print(
            f"Válidas    : {len(matches)}"
        )
        print(
            f"Ignoradas  : {len(skipped)}"
        )

    if len(matches) < 3:
        raise RuntimeError(
            "Há menos de 3 partidas válidas. "
            "Não há amostra suficiente para o diagnóstico."
        )

    classifications = ItemClassificationProvider(
        project_root=ROOT
    ).get()

    contest = ContestHistoryAnalyzer.analyze(
        matches
    )

    history = CompositionHistoryAnalyzer.analyze(
        matches,
        contest_history=contest,
        item_classifications=classifications,
    )

    report = CompositionIntelligenceV2.build(
        history
    )

    print()
    print("=" * 104)
    print(
        "#25 COMPOSITION INTELLIGENCE V2 - REAL"
    )
    print("=" * 104)

    print(
        f"Jogador              : "
        f"{game}#{tag}"
    )
    print(
        f"Partidas válidas     : "
        f"{report.matches_analyzed}"
    )
    print(
        f"Partidas ignoradas   : "
        f"{len(skipped)}"
    )
    print(
        f"Comps identificadas  : "
        f"{report.unique_compositions}"
    )
    print(
        f"Diversidade          : "
        f"{report.diversity_rate:.2f}%"
    )
    print(
        f"Repetição            : "
        f"{report.repetition_rate:.2f}%"
    )
    print(
        f"Sinal de repetição   : "
        f"{report.repetition_signal}"
    )
    print(
        f"Leitura              : "
        f"{report.repetition_interpretation}"
    )

    if skipped:
        print()
        print(
            "PARTIDAS IGNORADAS"
        )
        print(
            "-" * 104
        )

        for match_id, reason in skipped:
            print(
                f"- {match_id}: {reason}"
            )

    print()
    print(
        "COMPOSIÇÕES IDENTIFICADAS"
    )
    print(
        "-" * 104
    )

    for index, profile in enumerate(
        report.profiles,
        1,
    ):
        contest_value = (
            profile.average_contest_score
            if profile.average_contest_score is not None
            else "-"
        )

        print()
        print(
            f"[{index}] "
            f"{profile.composition_key}"
        )
        print(
            f"  Carry              : "
            f"{profile.carry_character_id or '-'}"
        )
        print(
            f"  Tank               : "
            f"{profile.tank_character_id or '-'}"
        )
        print(
            f"  Support            : "
            f"{profile.support_character_id or '-'}"
        )
        print(
            f"  Traits             : "
            f"{', '.join(profile.primary_trait_names) or '-'}"
        )
        print(
            f"  Core units         : "
            f"{', '.join(profile.core_unit_ids) or '-'}"
        )
        print(
            f"  Partidas           : "
            f"{profile.matches_played}"
        )
        print(
            f"  Uso                : "
            f"{profile.usage_rate:.2f}%"
        )
        print(
            f"  Colocação média    : "
            f"{profile.average_placement:.2f}"
        )
        print(
            f"  Top 4              : "
            f"{profile.top4_rate:.2f}%"
        )
        print(
            f"  Vitória            : "
            f"{profile.win_rate:.2f}%"
        )
        print(
            f"  Contestação média  : "
            f"{contest_value}"
        )
        print(
            f"  Confiança          : "
            f"{profile.confidence_score:.2f}% · "
            f"{profile.confidence_level}"
        )
        print(
            f"  Recomendação       : "
            f"{profile.recommendation_score:.2f} · "
            f"{profile.recommendation_label}"
        )
        print(
            f"  Amostra confiável  : "
            f"{'Sim' if profile.sample_is_reliable else 'Não'}"
        )

    print()
    print(
        "MAIS USADA"
    )
    print(
        "-" * 104
    )
    print(
        f"{report.most_used.composition_key} · "
        f"{report.most_used.matches_played} partidas · "
        f"carry {report.most_used.carry_character_id}"
    )

    print()
    print(
        "MELHOR COM AMOSTRA MÍNIMA"
    )
    print(
        "-" * 104
    )

    if report.best_supported:
        profile = report.best_supported

        print(
            f"{profile.composition_key} · "
            f"média {profile.average_placement:.2f} · "
            f"Top4 {profile.top4_rate:.2f}% · "
            f"{profile.matches_played} partidas"
        )

    else:
        print(
            "Nenhuma composição atingiu a "
            "amostra mínima de 3 partidas."
        )

    print()
    print(
        "LIMITAÇÕES"
    )
    print(
        "-" * 104
    )

    for item in report.limitations:
        print(
            "-",
            item,
        )

    print()
    print("=" * 104)
    print(
        "DIAGNÓSTICO CONCLUÍDO"
    )
    print(
        "Envie desde "
        "'#25 COMPOSITION INTELLIGENCE V2 - REAL' "
        "até o final."
    )
    print("=" * 104)


if __name__ == "__main__":
    main()
