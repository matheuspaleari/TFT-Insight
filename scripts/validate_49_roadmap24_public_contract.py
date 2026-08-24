from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = ROOT / ".gitignore"


if not GITIGNORE.exists():
    raise SystemExit("ERRO: .gitignore ausente")


text = GITIGNORE.read_text(
    encoding="utf-8-sig"
)


required_rules = (
    ".env",
    ".streamlit/secrets.toml",
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    "data/cache/",
    "data/debug/",
    "data/diagnostics/",
    "data/history/",
    "data/players/",
    "data/knowledge/*.db",
    "data/partner/*.db",
    "database/*.db",
    "data/processed/*",
    "!data/processed/.gitkeep",
    "data/raw/*",
    "!data/raw/.gitkeep",
    "estrutura.txt",
    "estrutura_tft_insight.txt",
)


protected_product_paths = (
    "data/benchmark/",
    "data/benchmarks/",
    "data/static_data/",
    "assets/",
)


checks = [
    (
        f"Protege {rule}",
        rule in text,
    )
    for rule in required_rules
]


for path in protected_product_paths:
    checks.append(
        (
            f"Não ignora produto: {path}",
            (
                f"\n{path}\n"
                not in f"\n{text}\n"
                and f"\n{path}*" not in f"\n{text}"
            ),
        )
    )


checks.extend(
    (
        (
            "Mantém exemplo de ambiente versionável",
            "!.env.example" in text,
        ),
        (
            "Mantém .gitkeep de processed",
            "!data/processed/.gitkeep" in text,
        ),
        (
            "Mantém .gitkeep de raw",
            "!data/raw/.gitkeep" in text,
        ),
    )
)


print("=" * 108)
print("#49 / ROADMAP 24.2 - SEGURANÇA + CONTRATO PÚBLICO")
print("=" * 108)


passed = 0


for index, (label, ok) in enumerate(
    checks,
    1,
):
    passed += int(ok)

    print(
        f"[{index:02d}] "
        f"{label:<76} "
        f"{'OK' if ok else 'ERRO'}"
    )


print("-" * 108)
print(
    f"PASSARAM: "
    f"{passed}/{len(checks)}"
)


if passed != len(checks):
    print(
        "#49 ROADMAP 24.2: REVISAR"
    )
    raise SystemExit(1)


print(
    "#49 ROADMAP 24.2: "
    "CONTRATO PÚBLICO VALIDADO"
)
