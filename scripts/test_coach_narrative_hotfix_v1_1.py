from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "partner_platform/pages/benchmark_page.py"


def _extract_function_source(
    text: str,
    function_name: str,
) -> str:
    tree = ast.parse(text)
    lines = text.splitlines()

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            end = getattr(node, "end_lineno", None)
            if end is None:
                raise RuntimeError(
                    f"Sem end_lineno para {function_name}"
                )
            return "\n".join(
                lines[node.lineno - 1:end]
            )

    raise RuntimeError(
        f"Função {function_name} não encontrada."
    )


def _load_public_text_for_behavior(text: str):
    source = "import re\n\n" + _extract_function_source(
        text,
        "_public_coach_text",
    )
    namespace = {}
    exec(source, namespace)
    return namespace["_public_coach_text"]


def main() -> None:
    text = PAGE.read_text(encoding="utf-8")
    ast.parse(text)

    public_text = _load_public_text_for_behavior(
        text
    )

    samples = {
        "Contestação": "Contestação",
        "contestação": "contestação",
        "contestado": "contestado",
        "contestada": "contestada",
        "contestados": "contestados",
        "contestadas": "contestadas",
        "Contestaçãoação": "Contestação",
        "contestaçãoado": "contestado",
        "contestaçãoada": "contestada",
        "contestaçãoados": "contestados",
        "contestaçãoadas": "contestadas",
        "contest": "contestação",
        "contest score": "índice de contestação",
    }

    semantic_ok = all(
        public_text(source) == expected
        for source, expected in samples.items()
    )

    checks = [
        (
            "Página compila",
            True,
        ),
        (
            "Não usa replace destrutivo de contest",
            '.replace("contest", "contestação")' not in text
            and '.replace("Contest", "Contestação")' not in text,
        ),
        (
            "Tradução usa regex com fronteira",
            r"\\bcontest\\b" in text,
        ),
        (
            "Corrige artefatos legados",
            "Contestaçãoação" in text
            and "contestaçãoado" in text,
        ),
        (
            "Semântica de contestação validada",
            semantic_ok,
        ),
        (
            "Missão ganha prioridade na próxima partida",
            "def _mission_first_next_focus(" in text,
        ),
        (
            "Próxima ação lê objective da missão",
            'summary.get("objective")' in text,
        ),
        (
            "Estratégia vira sinal complementar",
            "Como sinal complementar" in text,
        ),
        (
            "Fusion controla forças do narrador",
            "def _fusion_strength_message_filter(" in text,
        ),
        (
            "Sem força aprovada remove role strength",
            'item.get("role") != "strength"' in text,
        ),
        (
            "Narrador recebe mensagens filtradas",
            "narrator_messages" in text,
        ),
        (
            "Fallback também respeita filtro",
            "_build_coach_fallback_narrative(\n            narrator_messages," in text,
        ),
        (
            "Narrativa recebe fusion",
            "fusion=fusion" not in text
            and "fusion=(" in text,
        ),
        (
            "Narrativa recebe training",
            "training=(" in text,
        ),
        (
            "UI pública usa Contestação",
            '"Contestação"' in text,
        ),
    ]

    print("=" * 88)
    print("TFT INSIGHT - COACH NARRATIVE HOTFIX V1.1")
    print("=" * 88)

    passed = 0

    for index, (name, ok) in enumerate(checks, 1):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(f"Status  : {'OK' if ok else 'ERRO'}")

    print()
    print("=" * 88)
    print(f"PASSARAM: {passed}/{len(checks)}")

    if passed == len(checks):
        print("COACH NARRATIVE HOTFIX V1.1: VALIDADO")
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
