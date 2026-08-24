from pathlib import Path
import ast
import sys

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

TARGETS = (
    PROJECT_ROOT
    / "partner_platform"
)


def _contains_html_literal(
    node: ast.AST,
) -> bool:
    for child in ast.walk(node):
        if (
            isinstance(
                child,
                ast.Constant,
            )
            and isinstance(
                child.value,
                str,
            )
            and "<" in child.value
            and ">" in child.value
        ):
            return True

    return False


def main() -> None:
    violations: list[str] = []

    for path in TARGETS.rglob(
        "*.py"
    ):
        relative = path.relative_to(
            PROJECT_ROOT
        )

        # Theme is allowed to inject the stylesheet itself.
        if relative.as_posix() == (
            "partner_platform/theme/theme.py"
        ):
            continue

        source = path.read_text(
            encoding="utf-8"
        )

        try:
            tree = ast.parse(
                source,
                filename=str(path),
            )
        except SyntaxError as error:
            violations.append(
                f"{relative}: syntax error: {error}"
            )
            continue

        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            func = node.func

            is_markdown = (
                isinstance(
                    func,
                    ast.Attribute,
                )
                and func.attr == "markdown"
            )

            if (
                is_markdown
                and _contains_html_literal(
                    node
                )
            ):
                violations.append(
                    f"{relative}:{node.lineno} "
                    "raw HTML passed directly to markdown"
                )

    print("=" * 92)
    print(
        "TFT INSIGHT - PARTNER PLATFORM HTML AUDIT"
    )
    print("=" * 92)

    if violations:
        for violation in violations:
            print(
                f"FAIL: {violation}"
            )

        raise SystemExit(
            f"\n{len(violations)} violation(s) found."
        )

    print(
        "Raw HTML outside render_html : 0"
    )
    print(
        "Theme stylesheet exception   : OK"
    )
    print()
    print(
        "✓ HTML audit passed."
    )


if __name__ == "__main__":
    main()
