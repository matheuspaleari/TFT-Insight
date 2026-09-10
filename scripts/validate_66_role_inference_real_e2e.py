from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.integration_engine.services.item_classification_provider import (
    ItemClassificationProvider,
)
from src.role_inference.repositories.unit_catalog_repository import (
    UnitCatalogRepository,
)
from src.role_inference.services.role_inference_engine import (
    RoleInferenceEngine,
)
from src.transformers.match_transformer import MatchTransformer


STATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "role_inference"
    / "challenger"
)

MATCH_DIR = STATE_DIR / "matches"
MATCH_INDEX_PATH = STATE_DIR / "match_index.json"

TARGET_SET_NUMBER = 18
MAX_MATCHES = 100


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[OK] {label}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def set_number(payload: dict[str, Any]) -> int | None:
    info = payload.get("info")
    if not isinstance(info, dict):
        return None

    raw = info.get("tft_set_number")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def match_id_from_payload(
    payload: dict[str, Any],
    fallback: str,
) -> str:
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        value = str(metadata.get("match_id") or "").strip()
        if value:
            return value

    return fallback


def puuid_from_index(
    *,
    index: dict[str, Any],
    match_id: str,
) -> str:
    mapping = index.get("match_ids")

    if isinstance(mapping, dict):
        value = str(mapping.get(match_id) or "").strip()
        if value:
            return value

    return ""


def puuid_from_payload(payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata")

    if isinstance(metadata, dict):
        participants = metadata.get("participants")

        if isinstance(participants, list):
            for value in participants:
                clean = str(value or "").strip()
                if clean:
                    return clean

    info = payload.get("info")
    if isinstance(info, dict):
        participants = info.get("participants")

        if isinstance(participants, list):
            for participant in participants:
                if not isinstance(participant, dict):
                    continue

                clean = str(
                    participant.get("puuid") or ""
                ).strip()

                if clean:
                    return clean

    return ""


def friendly_name(character_id: str) -> str:
    return UnitCatalogRepository.display_name(
        character_id=character_id,
        fallback="",
    )


def main() -> None:
    print("=" * 92)
    print("VALIDAÇÃO 66 — END-TO-END REAL: PROVIDER → CACHE → TRANSFORMER → ROLE INFERENCE")
    print("=" * 92)

    check(
        MATCH_DIR.exists(),
        "cache Challenger de partidas encontrado",
    )

    cache_files = sorted(MATCH_DIR.glob("*.json"))

    check(
        bool(cache_files),
        "existem partidas reais em cache",
    )

    if MATCH_INDEX_PATH.exists():
        raw_index = load_json(MATCH_INDEX_PATH)
        index = raw_index if isinstance(raw_index, dict) else {}
        print("[OK] match_index.json encontrado")
    else:
        index = {}
        print(
            "[AVISO] match_index.json não encontrado; "
            "o teste tentará obter um PUUID do próprio payload"
        )

    # Provider real da aplicação.
    ItemClassificationProvider._classifications = None
    classifications = ItemClassificationProvider(
        project_root=PROJECT_ROOT,
    ).get()

    manual_count = sum(
        1
        for classification in classifications.values()
        if classification.source == "manual_set18_catalog_v2"
    )

    check(
        manual_count == 139,
        "provider real expõe os 139 itens manuais V2",
    )

    unit_catalog = UnitCatalogRepository.load_all(
        force_reload=True,
    )

    check(
        bool(unit_catalog),
        "catálogo manual de unidades Set 18 carregado",
    )

    scanned = 0
    transformed = 0
    target_set = 0
    failed_transform = 0
    missing_puuid = 0
    participants_with_units = 0
    selected_carries = 0
    selected_tanks = 0
    selected_supports = 0
    no_carry = 0
    uncatalogued_units = 0
    selected_noneligible_carries: list[str] = []
    friendly_name_failures: list[str] = []
    transform_errors: list[str] = []

    sample_rows: list[str] = []

    for path in cache_files:
        if transformed >= MAX_MATCHES:
            break

        scanned += 1

        try:
            payload = load_json(path)
        except Exception as exc:
            transform_errors.append(
                f"{path.name}: JSON inválido ({exc})"
            )
            failed_transform += 1
            continue

        if not isinstance(payload, dict):
            failed_transform += 1
            transform_errors.append(
                f"{path.name}: payload não é objeto"
            )
            continue

        if set_number(payload) != TARGET_SET_NUMBER:
            continue

        target_set += 1

        match_id = match_id_from_payload(
            payload,
            path.stem,
        )

        puuid = puuid_from_index(
            index=index,
            match_id=match_id,
        )

        if not puuid:
            puuid = puuid_from_payload(payload)

        if not puuid:
            missing_puuid += 1
            continue

        try:
            match = MatchTransformer.transform(
                match_data=payload,
                puuid=puuid,
            )
        except Exception as exc:
            failed_transform += 1
            transform_errors.append(
                f"{path.name}: {type(exc).__name__}: {exc}"
            )
            continue

        transformed += 1

        participant = match.analyzed_participant

        if participant is None:
            continue

        if participant.units:
            participants_with_units += 1

        for unit in participant.units:
            entry = unit_catalog.get(unit.character_id)
            if entry is None:
                uncatalogued_units += 1

        report = RoleInferenceEngine.infer_participant(
            participant=participant,
            item_classifications=classifications,
        )

        carry = report.damage_carry
        tank = report.main_tank
        support = report.support

        if carry is None:
            no_carry += 1
        else:
            selected_carries += 1

            entry = unit_catalog.get(carry.character_id)

            if entry is None or not entry.carry_eligible:
                selected_noneligible_carries.append(
                    carry.character_id
                )

            name = friendly_name(carry.character_id)

            if (
                not name
                or name == carry.character_id
                or name == "Unidade"
            ):
                friendly_name_failures.append(
                    carry.character_id
                )

        if tank is not None:
            selected_tanks += 1

            name = friendly_name(tank.character_id)
            if (
                not name
                or name == tank.character_id
                or name == "Unidade"
            ):
                friendly_name_failures.append(
                    tank.character_id
                )

        if support is not None:
            selected_supports += 1

            name = friendly_name(support.character_id)
            if (
                not name
                or name == support.character_id
                or name == "Unidade"
            ):
                friendly_name_failures.append(
                    support.character_id
                )

        if len(sample_rows) < 12:
            carry_name = (
                friendly_name(carry.character_id)
                if carry is not None
                else "—"
            )
            tank_name = (
                friendly_name(tank.character_id)
                if tank is not None
                else "—"
            )
            support_name = (
                friendly_name(support.character_id)
                if support is not None
                else "—"
            )

            sample_rows.append(
                f"{match_id} | "
                f"carry={carry_name} | "
                f"tank={tank_name} | "
                f"support={support_name}"
            )

    check(
        target_set > 0,
        "cache contém partidas do Set 18",
    )

    check(
        transformed > 0,
        "partidas reais do Set 18 foram transformadas",
    )

    check(
        participants_with_units > 0,
        "participantes reais com unidades foram analisados",
    )

    check(
        not selected_noneligible_carries,
        "nenhum campeão não elegível foi selecionado como carry",
    )

    check(
        not friendly_name_failures,
        "seleções possuem display_name amigável no catálogo",
    )

    check(
        selected_carries + no_carry == transformed,
        "cada partida transformada terminou com carry válido ou ausência explícita de carry",
    )

    print()
    print("-" * 92)
    print("AMOSTRA REAL — NOMES AMIGÁVEIS")
    print("-" * 92)

    for row in sample_rows:
        print(row)

    print()
    print("-" * 92)
    print("RESUMO")
    print("-" * 92)
    print(f"Arquivos de cache vistos       : {scanned}")
    print(f"Partidas Set 18 encontradas    : {target_set}")
    print(f"Partidas transformadas         : {transformed}")
    print(f"Falhas de transformação        : {failed_transform}")
    print(f"Sem PUUID resolvido            : {missing_puuid}")
    print(f"Com carry válido               : {selected_carries}")
    print(f"Sem carry (explícito)          : {no_carry}")
    print(f"Com tank selecionado           : {selected_tanks}")
    print(f"Com support selecionado        : {selected_supports}")
    print(f"Unidades fora do catálogo      : {uncatalogued_units}")
    print(f"Carries não elegíveis          : {len(selected_noneligible_carries)}")
    print(f"Falhas de display_name         : {len(friendly_name_failures)}")

    if transform_errors:
        print()
        print("Primeiras falhas de transformação:")
        for error in transform_errors[:10]:
            print(f"  - {error}")

    print()
    print("=" * 92)
    print("RESULTADO: FLUXO REAL V2 VALIDADO ATÉ O ROLE INFERENCE")
    print("=" * 92)


if __name__ == "__main__":
    main()
