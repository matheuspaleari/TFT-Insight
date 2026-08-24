from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "partner_platform/intelligence/local_coach_narrator.py"


def _class_method_source(
    text: str,
    class_name: str,
    method_name: str,
) -> str:
    tree = ast.parse(text)
    lines = text.splitlines()

    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name == class_name
        ):
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef)
                    and item.name == method_name
                ):
                    return "\n".join(
                        lines[
                            item.lineno - 1:
                            item.end_lineno
                        ]
                    )

    raise RuntimeError(
        f"{class_name}.{method_name} não encontrado"
    )


def main() -> None:
    text = FILE.read_text(
        encoding="utf-8"
    )
    ast.parse(text)

    checks = [
        (
            "Narrador compila",
            True,
        ),
        (
            "Prompt define uma única prioridade",
            "Existe somente UMA prioridade oficial de treino por vez"
            in text,
        ),
        (
            "Prompt proíbe outra prioridade",
            '"outra prioridade"' in text,
        ),
        (
            "Prompt transforma demais temas em sinal complementar",
            'apenas como "sinal complementar"' in text,
        ),
        (
            "Estrutura começa pela prioridade oficial",
            "Parágrafo 1: prioridade oficial de treino"
            in text,
        ),
        (
            "Próxima ação vem em seguida",
            "Parágrafo 2: ação prática da missão atual"
            in text,
        ),
        (
            "User prompt reforça prioridade única",
            "única prioridade oficial recebida"
            in text,
        ),
        (
            "User prompt proíbe segunda prioridade",
            "nunca como outra prioridade"
            in text,
        ),
        (
            "Limite de geração aumentado",
            '"num_predict": 480'
            in text,
        ),
        (
            "Validador detecta múltiplas prioridades",
            "def _uses_multiple_priority_language("
            in text,
        ),
        (
            "Validador detecta truncamento",
            "def _looks_truncated("
            in text,
        ),
        (
            "Outra prioridade é rejeitada",
            r"\boutra prioridade\b"
            in text,
        ),
        (
            "Resposta truncada é rejeitada",
            "resposta terminou no meio de uma frase"
            in text,
        ),
        (
            "Fallback continua disponível",
            "def _fallback_narrative("
            in text,
        ),
        (
            "Contest continua em português",
            'termo correto desta ferramenta é "contestação"'
            in text,
        ),
    ]

    print("=" * 90)
    print("TFT INSIGHT - COACH NARRATOR FINAL HOTFIX V1")
    print("=" * 90)

    passed = 0

    for index, (name, ok) in enumerate(
        checks,
        1,
    ):
        passed += int(ok)
        print()
        print(f"[{index}] {name}")
        print(
            f"Status  : {'OK' if ok else 'ERRO'}"
        )

    print()
    print("=" * 90)
    print(
        f"PASSARAM: {passed}/{len(checks)}"
    )

    if passed == len(checks):
        print(
            "COACH NARRATOR FINAL HOTFIX V1: VALIDADO"
        )
        raise SystemExit(0)

    raise SystemExit(1)


if __name__ == "__main__":
    main()
