from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]

SEARCH_ROOTS = (
    ROOT / "src",
    ROOT / "partner_platform",
)

SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    "archive",
    "roadmap_legacy",
}

TECHNICAL_ID_PATTERNS = (
    re.compile(r"\.character_id\b"),
    re.compile(r'\["character_id"\]'),
    re.compile(r"\.get\(\s*[\'\"]character_id[\'\"]"),
    re.compile(r"\bcarry_character_id\b"),
    re.compile(r"\bmost_used_carry_character_id\b"),
    re.compile(r"\blatest_carry\b"),
    re.compile(r"\bmain_tank\b"),
    re.compile(r"\bsupport\b"),
)

DISPLAY_HELPERS = (
    "friendly_game_name",
    "display_name",
    "UnitCatalogRepository",
)

UI_HINTS = (
    "st.",
    "render",
    "markdown",
    "write(",
    "caption",
    "title=",
    "value=",
    "label=",
    "headline",
    "summary",
    "evidence",
    "message",
    "text",
    "description",
)

API_HINTS = (
    "response_model",
    "return ",
    "payload",
    "dict(",
    "model_dump",
    "json",
)

ROLE_HINTS = (
    "damage_carry",
    "main_tank",
    "support",
    "carry",
    "tank",
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


def line_has_technical_id(line: str) -> bool:
    return any(pattern.search(line) for pattern in TECHNICAL_ID_PATTERNS)


def context(lines: list[str], index: int, radius: int = 4) -> list[tuple[int, str]]:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return [(i + 1, lines[i].rstrip()) for i in range(start, end)]


def classify(path: Path, lines: list[str], index: int) -> tuple[str, list[str]]:
    window_start = max(0, index - 5)
    window_end = min(len(lines), index + 6)
    window = "\n".join(lines[window_start:window_end])

    reasons = []

    uses_display_helper = any(helper in window for helper in DISPLAY_HELPERS)
    if uses_display_helper:
        reasons.append("display-helper-nearby")

    ui_context = (
        "partner_platform" in path.parts
        or any(hint in window for hint in UI_HINTS)
    )
    api_context = (
        "api" in path.parts
        or any(hint in window for hint in API_HINTS)
    )
    role_context = any(hint in window for hint in ROLE_HINTS)

    if ui_context:
        reasons.append("ui/presentation-context")
    if api_context:
        reasons.append("api/serialization-context")
    if role_context:
        reasons.append("role-context")

    # Strongest risk: technical role IDs flowing to UI/text with no resolver nearby.
    if role_context and ui_context and not uses_display_helper:
        return "HIGH", reasons

    # Medium: role IDs flowing through API/serialization without a nearby resolver.
    if role_context and api_context and not uses_display_helper:
        return "MEDIUM", reasons

    if uses_display_helper:
        return "SAFE", reasons

    return "LOW", reasons


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
            if not line_has_technical_id(line):
                continue

            risk, reasons = classify(path, lines, idx)
            findings.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "line": idx + 1,
                    "risk": risk,
                    "reasons": reasons,
                    "context": context(lines, idx),
                }
            )

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "SAFE": 3}
    findings.sort(key=lambda x: (order[x["risk"]], x["path"], x["line"]))

    counts = {
        risk: sum(1 for item in findings if item["risk"] == risk)
        for risk in ("HIGH", "MEDIUM", "LOW", "SAFE")
    }

    out_dir = ROOT / "data" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "audit_60_display_names_v2.txt"

    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("=" * 120 + "\n")
        fh.write("TFT INSIGHT — #60 AUDITORIA DISPLAY NAMES V2\n")
        fh.write("=" * 120 + "\n")
        fh.write(f"Arquivos Python auditados : {scanned_files}\n")
        fh.write(f"Linhas auditadas          : {scanned_lines}\n")
        fh.write(f"Referências técnicas      : {len(findings)}\n")
        fh.write(
            f"Risco                     : HIGH={counts['HIGH']} | "
            f"MEDIUM={counts['MEDIUM']} | LOW={counts['LOW']} | SAFE={counts['SAFE']}\n\n"
        )

        fh.write(
            "OBJETIVO\n"
            "Localizar pontos onde IDs técnicos de unidade/carry/tank/support podem chegar à API/UI.\n"
            "HIGH/MEDIUM são candidatos para revisão manual; não significam bug automaticamente.\n"
            "SAFE indica que há helper de display próximo do uso.\n"
            "Esta auditoria é somente leitura e não altera o projeto.\n\n"
        )

        for number, item in enumerate(findings, start=1):
            fh.write("-" * 120 + "\n")
            fh.write(
                f"[{number}] {item['risk']}  {item['path']}:{item['line']}\n"
            )
            fh.write(
                "Motivos: " + (", ".join(item["reasons"]) or "-") + "\n"
            )
            fh.write("-" * 120 + "\n")

            for line_no, content in item["context"]:
                pointer = ">>" if line_no == item["line"] else "  "
                fh.write(f"{pointer} {line_no:5d}: {content}\n")
            fh.write("\n")

        fh.write("=" * 120 + "\n")
        fh.write("RESUMO — ARQUIVOS HIGH/MEDIUM\n")
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
                lines = ", ".join(str(x["line"]) for x in items[:20])
                fh.write(
                    f"{path}\n"
                    f"  HIGH={high} | MEDIUM={medium} | linhas={lines}\n"
                )

    print("=" * 100)
    print("TFT INSIGHT — #60 AUDITORIA DISPLAY NAMES V2")
    print("=" * 100)
    print(f"Arquivos Python auditados : {scanned_files}")
    print(f"Linhas auditadas          : {scanned_lines}")
    print(f"Referências técnicas      : {len(findings)}")
    print(f"HIGH                      : {counts['HIGH']}")
    print(f"MEDIUM                    : {counts['MEDIUM']}")
    print(f"LOW                       : {counts['LOW']}")
    print(f"SAFE                      : {counts['SAFE']}")
    print()
    print(f"Relatório: {out_path.relative_to(ROOT)}")
    print("Nenhum arquivo do projeto foi alterado.")


if __name__ == "__main__":
    main()
