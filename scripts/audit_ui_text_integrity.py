from pathlib import Path
import re

ROOTS = [
    Path("partner_platform"),
]

MOJIBAKE_PATTERNS = (
    re.compile(r"Ã[\u0080-\u00BF]"),
    re.compile(r"Â[\u0080-\u00BF]"),
    re.compile(r"â(?:€|†|‡|—|–|™|œ|ž|Ÿ|€¢|„|“|”|˜|‰|€¦|ˆ|‹|›)"),
)
TECHNICAL_ID = re.compile(
    r"\b(?:TFT\d+_[A-Za-z0-9_]+|DA[ _-]*\d+[ _-]*[A-Za-z][A-Za-z0-9_-]*)\b",
    flags=re.IGNORECASE,
)

ALLOW_PATHS = {
    Path("partner_platform/utils/display_names.py"),
}


def main() -> None:
    findings = []

    for root in ROOTS:
        for path in root.rglob("*.py"):
            rel = path
            if rel in ALLOW_PATHS:
                continue

            text = path.read_text(encoding="utf-8")

            for number, line in enumerate(text.splitlines(), 1):
                if any(pattern.search(line) for pattern in MOJIBAKE_PATTERNS):
                    findings.append(
                        ("MOJIBAKE", path, number, line.strip())
                    )

                if TECHNICAL_ID.search(line):
                    findings.append(
                        ("TECHNICAL_ID", path, number, line.strip())
                    )

    if findings:
        print("REVISAR - foram encontrados possíveis vazamentos de UI:")
        for kind, path, number, line in findings:
            print(f"{kind}: {path}:{number}: {line}")
        raise SystemExit(1)

    print("OK - nenhuma sequência de mojibake ou ID técnico encontrada em partner_platform.")


if __name__ == "__main__":
    main()
