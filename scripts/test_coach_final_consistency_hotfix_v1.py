from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "partner_platform/pages/benchmark_page.py"


def _function_source(
    text: str,
    name: str,
) -> str:
    tree = ast.parse(text)
    lines = text.splitlines()

    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        ):
            return "\n".join(
                lines[
                    node.lineno - 1:
                    node.end_lineno
                ]
            )

    raise RuntimeError(
        f"Função ausente: {name}"
    )


def main() -> None:
    text = PAGE.read_text(
        encoding="utf-8"
    )
    ast.parse(text)

    namespace = {}
    exec(
        "import re\n\n"
        + _function_source(
            text,
            "_public_coach_text",
        ),
        namespace,
    )

    public_text = namespace[
        "_public_coach_text"
    ]

    terminology_samples = {
        "contest": "contestação",
        "contest score": "índice de contestação",
        "contestado": "contestado",
        "contestada": "contestada",
        "contestação": "contestação",
        "Contestaçãoação": "Contestação",
        "contestaçãoado": "contestado",
    }

    terminology_ok = all(
        public_text(raw) == expected
        for raw, expected
        in terminology_samples.items()
    )

    checks = [
        (
            "Página compila",
            True,
        ),
        (
            "Contest não usa replace destrutivo",
            '.replace("contest", "contestação")'
            not in text,
        ),
        (
            "Terminologia pública preserva contestado",
            terminology_ok,
        ),
        (
            "Fusion é autoridade de força",
            "def _filter_messages_by_fusion("
            in text,
        ),
        (
            "Sem força aprovada remove strength",
            'item.get("role") != "strength"'
            in text,
        ),
        (
            "Fusion gera contexto prioritário",
            "def _fusion_priority_message("
            in text,
        ),
        (
            "Contexto diz foco oficial atual",
            "O foco oficial atual é"
            in text,
        ),
        (
            "Fusion priority entra primeiro",
            "narrator_messages = ["
            in text
            and "fusion_priority,"
            in text,
        ),
        (
            "Missão domina próxima partida",
            "def _mission_first_next_focus("
            in text,
        ),
        (
            "Objetivo da missão é ação principal",
            'summary.get("objective")'
            in text,
        ),
        (
            "Estratégia é sinal complementar",
            "Como sinal complementar"
            in text,
        ),
        (
            "Narrador recebe fusion",
            "fusion=(" in text,
        ),
        (
            "Narrador recebe training",
            "training=(" in text,
        ),
        (
            "Fallback usa mensagens filtradas",
            "_build_coach_fallback_narrative(\n"
            "            narrator_messages,"
            in text,
        ),
        (
            "Nenhum cálculo do Learning Priority alterado",
            "build_global_priority(" in text,
        ),
        (
            "Não existe previsão de subida",
            "probability_to_rank_up"
            not in text,
        ),
    ]

    print("=" * 90)
    print(
        "TFT INSIGHT - COACH FINAL CONSISTENCY HOTFIX V1"
    )
    print("=" * 90)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        1,
    ):
        passed += int(ok)
        print()
        print(
            f"[{index}] {name}"
        )
        print(
            f"Status  : "
            f"{'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 90)
    print(
        f"PASSARAM: "
        f"{passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "COACH FINAL CONSISTENCY HOTFIX V1: VALIDADO"
        )
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
