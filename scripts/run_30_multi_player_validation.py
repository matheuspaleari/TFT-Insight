from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from partner_platform.components.pre_match_coach import (
    build_pre_match_coach,
)
from partner_platform.services.api_client import (
    DashboardApiClient,
)


GROUPS = (
    "intermediate",
    "advanced",
    "expert",
    "elite",
)

FORBIDDEN_COACH_FRAGMENTS = (
    "você errou porque",
    "deveria ter rolado",
    "deveria ter comprado xp",
    "causou sua derrota",
    "causou a derrota",
    "obrigatório pivotar",
)

REQUIRED_MODULES = (
    "composition",
    "contest",
    "economy",
    "carry_item",
)


@dataclass
class PlayerCase:
    benchmark_id: str
    game_name: str
    tag_line: str
    tier: str
    division: str
    league_points: int
    catalog_matches: int


@dataclass
class ModuleResult:
    ok: bool
    elapsed_seconds: float
    error: str = ""


@dataclass
class PlayerResult:
    benchmark_id: str
    game_name: str
    tag_line: str
    tier: str
    modules_ok: int
    modules_total: int
    coach_ok: bool
    identity_ok: bool
    payload_ok: bool
    overall_ok: bool
    composition_unique: int | None
    contest_carry_rate: float | None
    economy_level: float | None
    carry_unique: int | None
    elapsed_seconds: float
    errors: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Roadmap 19 / #30: valida o TFT Insight com "
            "jogadores de grupos competitivos diferentes."
        )
    )
    parser.add_argument(
        "--players-per-group",
        type=int,
        default=1,
        choices=(1, 2, 3),
        help=(
            "Quantidade de jogadores por grupo. "
            "Default 1 = 4 jogadores no total."
        ),
    )
    parser.add_argument(
        "--match-count",
        type=int,
        default=10,
        choices=(10, 20, 30),
        help=(
            "Partidas solicitadas por módulo. "
            "Use 10 no smoke test e 30 somente no teste profundo."
        ),
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.5,
        help="Pausa entre jogadores para reduzir pressão na API.",
    )
    parser.add_argument(
        "--only-group",
        choices=GROUPS,
        default=None,
        help="Executa apenas um grupo competitivo.",
    )
    return parser.parse_args()


def _safe_float(
    value: Any,
) -> float | None:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def _safe_int(
    value: Any,
) -> int | None:
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def _range(
    value: Any,
    low: float,
    high: float,
) -> bool:
    number = _safe_float(value)
    return (
        number is not None
        and low <= number <= high
    )


def load_cases(
    *,
    players_per_group: int,
    only_group: str | None,
) -> list[PlayerCase]:
    groups = (
        (only_group,)
        if only_group
        else GROUPS
    )

    cases: list[PlayerCase] = []

    for benchmark_id in groups:
        path = (
            ROOT
            / "data/benchmark"
            / f"{benchmark_id}_player_catalog.json"
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Catálogo não encontrado: {path}"
            )

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        players = [
            item
            for item in payload.get(
                "players",
                [],
            )
            if int(
                item.get(
                    "matches_used",
                    0,
                )
                or 0
            ) >= 10
            and str(
                item.get(
                    "game_name",
                    "",
                )
            ).strip()
            and str(
                item.get(
                    "tag_line",
                    "",
                )
            ).strip()
        ]

        # Ordem determinística: maior amostra, maior LP e Riot ID.
        players.sort(
            key=lambda item: (
                -int(
                    item.get(
                        "matches_used",
                        0,
                    )
                    or 0
                ),
                -int(
                    item.get(
                        "current_league_points",
                        0,
                    )
                    or 0
                ),
                str(
                    item.get(
                        "game_name",
                        "",
                    )
                ).lower(),
            )
        )

        selected = players[
            :players_per_group
        ]

        if len(selected) < players_per_group:
            raise RuntimeError(
                f"{benchmark_id}: catálogo não possui "
                f"{players_per_group} jogadores elegíveis."
            )

        for item in selected:
            cases.append(
                PlayerCase(
                    benchmark_id=benchmark_id,
                    game_name=str(
                        item.get(
                            "game_name",
                            "",
                        )
                    ),
                    tag_line=str(
                        item.get(
                            "tag_line",
                            "",
                        )
                    ),
                    tier=str(
                        item.get(
                            "current_tier",
                            item.get(
                                "tier_at_collection",
                                "-",
                            ),
                        )
                    ),
                    division=str(
                        item.get(
                            "current_division",
                            item.get(
                                "division_at_collection",
                                "-",
                            ),
                        )
                    ),
                    league_points=int(
                        item.get(
                            "current_league_points",
                            item.get(
                                "league_points_at_collection",
                                0,
                            ),
                        )
                        or 0
                    ),
                    catalog_matches=int(
                        item.get(
                            "matches_used",
                            0,
                        )
                        or 0
                    ),
                )
            )

    return cases


def build_client() -> DashboardApiClient:
    return DashboardApiClient(
        base_url=os.getenv(
            "TFT_INSIGHT_API_BASE_URL",
            "http://127.0.0.1:8000",
        ),
        api_key=os.getenv(
            "TFT_INSIGHT_API_KEY",
            "",
        ),
        timeout=300.0,
    )


def call_module(
    *,
    label: str,
    function: Callable[[], dict],
) -> tuple[dict | None, ModuleResult]:
    started = time.perf_counter()

    try:
        payload = function()
        elapsed = round(
            time.perf_counter()
            - started,
            2,
        )

        if not isinstance(
            payload,
            dict,
        ):
            return (
                None,
                ModuleResult(
                    ok=False,
                    elapsed_seconds=elapsed,
                    error=(
                        f"{label}: resposta não é dict."
                    ),
                ),
            )

        return (
            payload,
            ModuleResult(
                ok=True,
                elapsed_seconds=elapsed,
            ),
        )

    except Exception as error:
        elapsed = round(
            time.perf_counter()
            - started,
            2,
        )

        return (
            None,
            ModuleResult(
                ok=False,
                elapsed_seconds=elapsed,
                error=(
                    f"{label}: "
                    f"{type(error).__name__}: {error}"
                ),
            ),
        )


def identity_matches(
    payload: dict | None,
    case: PlayerCase,
) -> bool:
    if not isinstance(
        payload,
        dict,
    ):
        return False

    player = payload.get(
        "player",
        {},
    ) or {}

    return (
        str(
            player.get(
                "game_name",
                "",
            )
        ).strip().lower()
        == case.game_name.strip().lower()
        and str(
            player.get(
                "tag_line",
                "",
            )
        ).strip().lower()
        == case.tag_line.strip().lower()
    )


def validate_composition(
    payload: dict,
) -> list[str]:
    errors = []
    summary = payload.get(
        "summary",
        {},
    ) or {}

    matches = _safe_int(
        summary.get(
            "matches_analyzed"
        )
    )
    unique = _safe_int(
        summary.get(
            "unique_compositions"
        )
    )

    if (
        matches is None
        or matches < 3
    ):
        errors.append(
            "Composições: matches_analyzed inválido."
        )

    if (
        unique is None
        or unique < 1
        or (
            matches is not None
            and unique > matches
        )
    ):
        errors.append(
            "Composições: unique_compositions inválido."
        )

    for key in (
        "diversity_rate",
        "repetition_rate",
    ):
        if not _range(
            summary.get(key),
            0.0,
            100.0,
        ):
            errors.append(
                f"Composições: {key} fora de 0..100."
            )

    return errors


def validate_contest(
    payload: dict,
) -> list[str]:
    errors = []
    summary = payload.get(
        "summary",
        {},
    ) or {}

    for key in (
        "high_contest_rate",
        "carry_contest_rate",
    ):
        if not _range(
            summary.get(key),
            0.0,
            100.0,
        ):
            errors.append(
                f"Contestação: {key} fora de 0..100."
            )

    average_score = _safe_float(
        summary.get(
            "average_score"
        )
    )

    if (
        average_score is None
        or average_score < 0
    ):
        errors.append(
            "Contestação: average_score inválido."
        )

    return errors


def validate_economy(
    payload: dict,
) -> list[str]:
    errors = []
    summary = payload.get(
        "summary",
        {},
    ) or {}

    level = _safe_float(
        summary.get(
            "average_level"
        )
    )

    if (
        level is None
        or not 1.0 <= level <= 11.0
    ):
        errors.append(
            "Economia: average_level fora de faixa."
        )

    gold = _safe_float(
        summary.get(
            "average_gold_left"
        )
    )

    if (
        gold is None
        or gold < 0
    ):
        errors.append(
            "Economia: average_gold_left inválido."
        )

    for key in (
        "level_8_rate",
        "level_9_rate",
        "low_level_late_rate",
    ):
        if not _range(
            summary.get(key),
            0.0,
            100.0,
        ):
            errors.append(
                f"Economia: {key} fora de 0..100."
            )

    return errors


def validate_carry_item(
    payload: dict,
) -> list[str]:
    errors = []
    summary = payload.get(
        "summary",
        {},
    ) or {}

    for key in (
        "carry_detection_rate",
        "carry_item_share",
        "carry_full_item_rate",
    ):
        if not _range(
            summary.get(key),
            0.0,
            100.0,
        ):
            errors.append(
                f"Carries/Itens: {key} fora de 0..100."
            )

    matches_with_carry = _safe_int(
        summary.get(
            "matches_with_carry"
        )
    )
    unique_carries = _safe_int(
        summary.get(
            "unique_carries"
        )
    )

    if (
        matches_with_carry is not None
        and unique_carries is not None
        and unique_carries > matches_with_carry
    ):
        errors.append(
            "Carries/Itens: mais carries únicos que partidas com carry."
        )

    return errors


def validate_coach(
    *,
    composition: dict,
    contest: dict,
    economy: dict,
    carry_item: dict,
) -> tuple[bool, list[str], dict]:
    training = {
        "skill_label": "Leveling",
        "mission_title": "Planejar o próximo nível",
        "objective": (
            "Antes de gastar ouro, defina qual será "
            "seu próximo momento de subida de nível."
        ),
    }

    coach = build_pre_match_coach(
        training=training,
        composition=composition,
        contest=contest,
        economy=economy,
        carry_item=carry_item,
    )

    errors = []

    if coach.get(
        "skill"
    ) != training[
        "skill_label"
    ]:
        errors.append(
            "Coach alterou o foco."
        )

    if coach.get(
        "mission"
    ) != training[
        "mission_title"
    ]:
        errors.append(
            "Coach alterou a missão."
        )

    support = coach.get(
        "support",
        [],
    )

    labels = {
        str(
            item.get(
                "label",
                "",
            )
        )
        for item in support
        if isinstance(
            item,
            dict,
        )
    }

    expected = {
        "Composições",
        "Contestação",
        "Economia",
        "Carries e itens",
    }

    if not expected.issubset(
        labels
    ):
        errors.append(
            "Coach não consolidou os quatro módulos."
        )

    public_text = json.dumps(
        coach,
        ensure_ascii=False,
    ).lower()

    for fragment in FORBIDDEN_COACH_FRAGMENTS:
        if fragment in public_text:
            errors.append(
                "Coach contém inferência proibida: "
                + fragment
            )

    return (
        not errors,
        errors,
        coach,
    )


def module_fingerprint(
    *,
    composition: dict,
    contest: dict,
    economy: dict,
    carry_item: dict,
) -> tuple:
    comp = composition.get(
        "summary",
        {},
    ) or {}
    con = contest.get(
        "summary",
        {},
    ) or {}
    eco = economy.get(
        "summary",
        {},
    ) or {}
    car = carry_item.get(
        "summary",
        {},
    ) or {}

    return (
        _safe_int(
            comp.get(
                "unique_compositions"
            )
        ),
        _safe_float(
            comp.get(
                "diversity_rate"
            )
        ),
        _safe_float(
            con.get(
                "carry_contest_rate"
            )
        ),
        _safe_float(
            eco.get(
                "average_level"
            )
        ),
        _safe_float(
            eco.get(
                "average_gold_left"
            )
        ),
        _safe_int(
            car.get(
                "unique_carries"
            )
        ),
    )


def main() -> None:
    args = parse_args()

    print(
        "="
        * 116
    )
    print(
        "#30 / ROADMAP 19 - TESTES COM JOGADORES DIFERENTES"
    )
    print(
        "="
        * 116
    )
    print(
        f"Jogadores por grupo : {args.players_per_group}"
    )
    print(
        f"Partidas por módulo : {args.match_count}"
    )
    print(
        "Grupos              : "
        + (
            args.only_group
            if args.only_group
            else ", ".join(
                GROUPS
            )
        )
    )

    cases = load_cases(
        players_per_group=args.players_per_group,
        only_group=args.only_group,
    )

    print()
    print(
        "COORTE"
    )
    print(
        "-"
        * 116
    )

    for case in cases:
        print(
            f"{case.benchmark_id:<13} | "
            f"{case.game_name}#{case.tag_line:<12} | "
            f"{case.tier} {case.division} {case.league_points} LP | "
            f"catálogo={case.catalog_matches}"
        )

    client = build_client()

    output_dir = (
        ROOT
        / "data/diagnostics/multi_player_validation"
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    raw_report: dict[str, Any] = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "players_per_group": args.players_per_group,
        "match_count": args.match_count,
        "players": [],
    }

    results: list[PlayerResult] = []
    fingerprints: dict[
        tuple,
        list[str],
    ] = {}

    for index, case in enumerate(
        cases,
        1,
    ):
        player_started = time.perf_counter()

        print()
        print(
            "="
            * 116
        )
        print(
            f"[{index}/{len(cases)}] "
            f"{case.game_name}#{case.tag_line} "
            f"({case.benchmark_id} / {case.tier})"
        )
        print(
            "="
            * 116
        )

        modules: dict[
            str,
            dict | None,
        ] = {}
        module_results: dict[
            str,
            ModuleResult,
        ] = {}

        module_calls = {
            "composition": (
                lambda: client.composition_intelligence(
                    game_name=case.game_name,
                    tag_line=case.tag_line,
                    match_count=args.match_count,
                )
            ),
            "contest": (
                lambda: client.contest_intelligence(
                    game_name=case.game_name,
                    tag_line=case.tag_line,
                    match_count=args.match_count,
                )
            ),
            "economy": (
                lambda: client.economy_intelligence(
                    game_name=case.game_name,
                    tag_line=case.tag_line,
                    match_count=args.match_count,
                )
            ),
            "carry_item": (
                lambda: client.carry_item_intelligence(
                    game_name=case.game_name,
                    tag_line=case.tag_line,
                    match_count=args.match_count,
                )
            ),
        }

        for module_name in REQUIRED_MODULES:
            payload, call_result = call_module(
                label=module_name,
                function=module_calls[
                    module_name
                ],
            )

            modules[
                module_name
            ] = payload
            module_results[
                module_name
            ] = call_result

            print(
                f"{module_name:<14}: "
                f"{'OK' if call_result.ok else 'ERRO'} "
                f"({call_result.elapsed_seconds:.2f}s)"
            )

            if not call_result.ok:
                print(
                    "  "
                    + call_result.error
                )

        errors: list[str] = []

        modules_ok = sum(
            result.ok
            for result in module_results.values()
        )

        identity_ok = all(
            identity_matches(
                modules[
                    module_name
                ],
                case,
            )
            for module_name in REQUIRED_MODULES
            if modules[
                module_name
            ] is not None
        ) and modules_ok == len(
            REQUIRED_MODULES
        )

        if not identity_ok:
            errors.append(
                "Identidade retornada pela API não bate com o jogador solicitado."
            )

        payload_ok = False
        coach_ok = False
        coach_payload = None

        if modules_ok == len(
            REQUIRED_MODULES
        ):
            payload_errors = []
            payload_errors.extend(
                validate_composition(
                    modules[
                        "composition"
                    ]
                )
            )
            payload_errors.extend(
                validate_contest(
                    modules[
                        "contest"
                    ]
                )
            )
            payload_errors.extend(
                validate_economy(
                    modules[
                        "economy"
                    ]
                )
            )
            payload_errors.extend(
                validate_carry_item(
                    modules[
                        "carry_item"
                    ]
                )
            )

            payload_ok = not payload_errors
            errors.extend(
                payload_errors
            )

            (
                coach_ok,
                coach_errors,
                coach_payload,
            ) = validate_coach(
                composition=modules[
                    "composition"
                ],
                contest=modules[
                    "contest"
                ],
                economy=modules[
                    "economy"
                ],
                carry_item=modules[
                    "carry_item"
                ],
            )

            errors.extend(
                coach_errors
            )

            fingerprint = module_fingerprint(
                composition=modules[
                    "composition"
                ],
                contest=modules[
                    "contest"
                ],
                economy=modules[
                    "economy"
                ],
                carry_item=modules[
                    "carry_item"
                ],
            )

            fingerprints.setdefault(
                fingerprint,
                [],
            ).append(
                f"{case.game_name}#{case.tag_line}"
            )

        for module_name, result in module_results.items():
            if result.error:
                errors.append(
                    result.error
                )

        composition_unique = None
        contest_carry_rate = None
        economy_level = None
        carry_unique = None

        if modules.get(
            "composition"
        ):
            composition_unique = _safe_int(
                (
                    modules[
                        "composition"
                    ].get(
                        "summary",
                        {},
                    )
                    or {}
                ).get(
                    "unique_compositions"
                )
            )

        if modules.get(
            "contest"
        ):
            contest_carry_rate = _safe_float(
                (
                    modules[
                        "contest"
                    ].get(
                        "summary",
                        {},
                    )
                    or {}
                ).get(
                    "carry_contest_rate"
                )
            )

        if modules.get(
            "economy"
        ):
            economy_level = _safe_float(
                (
                    modules[
                        "economy"
                    ].get(
                        "summary",
                        {},
                    )
                    or {}
                ).get(
                    "average_level"
                )
            )

        if modules.get(
            "carry_item"
        ):
            carry_unique = _safe_int(
                (
                    modules[
                        "carry_item"
                    ].get(
                        "summary",
                        {},
                    )
                    or {}
                ).get(
                    "unique_carries"
                )
            )

        overall_ok = (
            modules_ok
            == len(
                REQUIRED_MODULES
            )
            and identity_ok
            and payload_ok
            and coach_ok
        )

        elapsed = round(
            time.perf_counter()
            - player_started,
            2,
        )

        result = PlayerResult(
            benchmark_id=case.benchmark_id,
            game_name=case.game_name,
            tag_line=case.tag_line,
            tier=case.tier,
            modules_ok=modules_ok,
            modules_total=len(
                REQUIRED_MODULES
            ),
            coach_ok=coach_ok,
            identity_ok=identity_ok,
            payload_ok=payload_ok,
            overall_ok=overall_ok,
            composition_unique=composition_unique,
            contest_carry_rate=contest_carry_rate,
            economy_level=economy_level,
            carry_unique=carry_unique,
            elapsed_seconds=elapsed,
            errors=errors,
        )

        results.append(
            result
        )

        raw_report[
            "players"
        ].append(
            {
                "case": asdict(
                    case
                ),
                "module_results": {
                    key: asdict(
                        value
                    )
                    for key, value
                    in module_results.items()
                },
                "modules": modules,
                "coach": coach_payload,
                "validation": asdict(
                    result
                ),
            }
        )

        print()
        print(
            "VALIDAÇÃO"
        )
        print(
            f"Identidade       : {'OK' if identity_ok else 'ERRO'}"
        )
        print(
            f"Payloads         : {'OK' if payload_ok else 'ERRO'}"
        )
        print(
            f"Coach consolidado: {'OK' if coach_ok else 'ERRO'}"
        )
        print(
            f"Resultado jogador: {'OK' if overall_ok else 'ERRO'}"
        )

        if errors:
            print(
                "Erros:"
            )
            for error in errors:
                print(
                    f"- {error}"
                )

        if (
            index
            < len(cases)
            and args.sleep > 0
        ):
            time.sleep(
                args.sleep
            )

    duplicate_fingerprints = [
        players
        for players in fingerprints.values()
        if len(players) > 1
    ]

    passed_players = sum(
        result.overall_ok
        for result in results
    )

    modules_passed = sum(
        result.modules_ok
        for result in results
    )
    modules_total = (
        len(results)
        * len(
            REQUIRED_MODULES
        )
    )

    cross_player_ok = (
        not duplicate_fingerprints
        or len(
            fingerprints
        ) >= max(
            2,
            len(results) // 2,
        )
    )

    raw_report[
        "summary"
    ] = {
        "players_passed": passed_players,
        "players_total": len(results),
        "module_calls_passed": modules_passed,
        "module_calls_total": modules_total,
        "distinct_fingerprints": len(
            fingerprints
        ),
        "duplicate_fingerprints": duplicate_fingerprints,
        "cross_player_variation_ok": cross_player_ok,
    }

    json_path = (
        output_dir
        / f"multi_player_validation_{timestamp}.json"
    )

    json_path.write_text(
        json.dumps(
            raw_report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    csv_path = (
        output_dir
        / f"multi_player_validation_{timestamp}.csv"
    )

    with csv_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "benchmark_id",
                "game_name",
                "tag_line",
                "tier",
                "modules_ok",
                "modules_total",
                "coach_ok",
                "identity_ok",
                "payload_ok",
                "overall_ok",
                "composition_unique",
                "contest_carry_rate",
                "economy_level",
                "carry_unique",
                "elapsed_seconds",
                "errors",
            ],
        )
        writer.writeheader()

        for result in results:
            row = asdict(
                result
            )
            row[
                "errors"
            ] = " | ".join(
                result.errors
            )
            writer.writerow(
                row
            )

    print()
    print(
        "="
        * 116
    )
    print(
        "RESUMO FINAL"
    )
    print(
        "="
        * 116
    )

    for result in results:
        print(
            f"{'OK' if result.overall_ok else 'ERRO':<5} | "
            f"{result.benchmark_id:<13} | "
            f"{result.game_name}#{result.tag_line:<12} | "
            f"mods {result.modules_ok}/{result.modules_total} | "
            f"coach={'OK' if result.coach_ok else 'ERRO'} | "
            f"{result.elapsed_seconds:.2f}s"
        )

    print()
    print(
        f"Jogadores aprovados      : "
        f"{passed_players}/{len(results)}"
    )
    print(
        f"Chamadas de módulos OK   : "
        f"{modules_passed}/{modules_total}"
    )
    print(
        f"Perfis distintos         : "
        f"{len(fingerprints)}/{len(results)}"
    )
    print(
        f"Variação entre jogadores : "
        f"{'OK' if cross_player_ok else 'REVISAR'}"
    )

    if duplicate_fingerprints:
        print()
        print(
            "Fingerprints idênticos encontrados:"
        )
        for players in duplicate_fingerprints:
            print(
                "- "
                + ", ".join(
                    players
                )
            )

    print()
    print(
        "ARQUIVOS GERADOS"
    )
    print(
        "-"
        * 116
    )
    print(
        json_path
    )
    print(
        csv_path
    )

    print()
    print(
        "="
        * 116
    )

    if (
        passed_players
        == len(results)
        and modules_passed
        == modules_total
        and cross_player_ok
    ):
        print(
            "#30 / ROADMAP 19 TESTES MULTI-JOGADOR: VALIDADO"
        )
        raise SystemExit(
            0
        )

    print(
        "#30 / ROADMAP 19 TESTES MULTI-JOGADOR: REVISAR"
    )
    raise SystemExit(
        1
    )


if __name__ == "__main__":
    main()
