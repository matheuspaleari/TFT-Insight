import subprocess
import sys


def main() -> None:
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "partner_platform/app.py",
    ]

    raise SystemExit(
        subprocess.call(command)
    )


if __name__ == "__main__":
    main()
