from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]

SEARCH_ROOTS = (
    ROOT / "src",
    ROOT / "partner_platform",
    ROOT / "scripts",
)

SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    "archive",
    "roadmap_legacy",
}

PATTERNS = {
    "carry_terms": re.compile(
        r"\b(carry|damage_carry|main_carry|primary_carry|secondary_carry)\b",
        re.IGNORECASE,
    ),
    "fallback_terms": re.compile(
        r"\b(fallback|default|backup|heuristic|guess|infer)\b",
        re.IGNORECASE,
    ),
    "ranking_terms": re.compile(
        r"\b(max|min|sorted|sort|key\s*=|len\s*\(|rarity|tier|items?|item_ids)\b",
        re.IGNORECASE,
    ),
    "selection_terms": re.compile(
        r"\b(select|selected|candidate|candidates|winner|best|choose|pick)\b",
        re.IGNORECASE,
    ),
}

HIGH_RISK_COMBOS = (
    ("carry_terms", "ranking_terms"),
    ("carry_terms", "fallback_terms"),
    ("carry_terms", "selection_terms"),
)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def iter_python_files():
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if should_skip(path):
                continue
            yield path


def classify_line(line: str) -> tuple[str, list[str]]:
    hits = [
        name
        for name, pattern in PATTERNS.items()
        if pattern.search(line)
    ]

    risk = "LOW"

    for left, right in HIGH_RISK_COMBOS:
        if left in hits and right in hits:
            risk = "HIGH"
            break

    if (
        risk != "HIGH"
        and "carry_terms" in hits
        and len(hits) >= 2
    ):
        risk = "MEDIUM"

    return risk, hits


def context(lines: list[str], index: int, radius: int = 3) -> list[tuple[int, str]]:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return [
        (i + 1, lines[i].rstrip())
        for i in range(start, end)
    ]


def main():
    findings = []
    scanned_files = 0
    scanned_lines = 0

    for path in iter_python_files():
        scanned_files += 1

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")

        lines = text.splitlines()
        scanned_lines += len(lines)

        for idx, line in enumerate(lines):
            risk, hits = classify_line(line)

            if not hits:
                continue

            if "carry_terms" not in hits:
                continue

            findings.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "line": idx + 1,
                    "risk": risk,
                    "hits": hits,
                    "context": context(lines, idx),
                }
            )

    findings.sort(
        key=lambda x: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["risk"]],
            x["path"],
            x["line"],
        )
    )

    out_dir = ROOT / "data" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "audit_59_carry_fallbacks.txt"

    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("=" * 120 + "\n")
        fh.write("TFT INSIGHT — #59 AUDITORIA DE FALLBACKS PARALELOS DE CARRY\n")
        fh.write("=" * 120 + "\n")
        fh.write(f"Arquivos Python auditados : {scanned_files}\n")
        fh.write(f"Linhas auditadas          : {scanned_lines}\n")
        fh.write(f"Ocorrências com 'carry'   : {len(findings)}\n")

        counts = {
            risk: sum(1 for x in findings if x["risk"] == risk)
            for risk in ("HIGH", "MEDIUM", "LOW")
        }

        fh.write(
            "Risco                    : "
            f"HIGH={counts['HIGH']} | "
            f"MEDIUM={counts['MEDIUM']} | "
            f"LOW={counts['LOW']}\n\n"
        )

        fh.write(
            "IMPORTANTE\n"
            "Esta auditoria é read-only. Ela não altera código, cache ou dados.\n"
            "HIGH/MEDIUM são candidatos para revisão manual; não significam bug automaticamente.\n"
            "O objetivo é localizar lugares onde carry possa ser escolhido fora do RoleInferenceEngine V2.\n\n"
        )

        for number, item in enumerate(findings, start=1):
            fh.write("-" * 120 + "\n")
            fh.write(
                f"[{number}] {item['risk']}  "
                f"{item['path']}:{item['line']}\n"
            )
            fh.write(
                f"Marcadores: {', '.join(item['hits'])}\n"
            )
            fh.write("-" * 120 + "\n")

            for line_no, content in item["context"]:
                pointer = ">>" if line_no == item["line"] else "  "
                fh.write(
                    f"{pointer} {line_no:5d}: {content}\n"
                )

            fh.write("\n")

        fh.write("=" * 120 + "\n")
        fh.write("RESUMO DE ARQUIVOS MAIS SUSPEITOS\n")
        fh.write("=" * 120 + "\n")

        grouped = {}
        for item in findings:
            if item["risk"] not in {"HIGH", "MEDIUM"}:
                continue
            grouped.setdefault(item["path"], []).append(item)

        ranked = sorted(
            grouped.items(),
            key=lambda kv: (
                -sum(1 for x in kv[1] if x["risk"] == "HIGH"),
                -sum(1 for x in kv[1] if x["risk"] == "MEDIUM"),
                kv[0],
            ),
        )

        if not ranked:
            fh.write("Nenhum candidato HIGH/MEDIUM encontrado.\n")
        else:
            for path, items in ranked:
                high = sum(1 for x in items if x["risk"] == "HIGH")
                medium = sum(1 for x in items if x["risk"] == "MEDIUM")
                lines = ", ".join(str(x["line"]) for x in items[:12])

                fh.write(
                    f"{path}\n"
                    f"  HIGH={high} | MEDIUM={medium} | "
                    f"linhas={lines}\n"
                )

    print("=" * 100)
    print("TFT INSIGHT — #59 AUDITORIA DE FALLBACKS PARALELOS DE CARRY")
    print("=" * 100)
    print(f"Arquivos Python auditados : {scanned_files}")
    print(f"Linhas auditadas          : {scanned_lines}")
    print(f"Ocorrências encontradas   : {len(findings)}")
    print(f"HIGH                      : {counts['HIGH']}")
    print(f"MEDIUM                    : {counts['MEDIUM']}")
    print(f"LOW                       : {counts['LOW']}")
    print()
    print(f"Relatório: {out_path.relative_to(ROOT)}")
    print()
    print("Não alterei nenhum arquivo do projeto.")


if __name__ == "__main__":
    main()
