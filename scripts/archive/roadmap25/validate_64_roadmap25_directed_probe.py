from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/probe_tft_lcu_directed_safe.py"
ANALYZER = ROOT / "scripts/analyze_tft_lcu_directed_probe.py"

probe_text = PROBE.read_text(encoding="utf-8") if PROBE.exists() else ""
analyzer_text = ANALYZER.read_text(encoding="utf-8") if ANALYZER.exists() else ""

FORBIDDEN = (
    "OpenProcess",
    "ReadProcessMemory",
    "WriteProcessMemory",
    "VirtualAllocEx",
    "CreateRemoteThread",
    "ctypes",
    "pymem",
    "frida",
    "win32process",
    "win32api",
    "scapy",
    "pydivert",
    "requests.post(",
    "requests.put(",
    "requests.patch(",
    "requests.delete(",
)

REQUIRED_ENDPOINTS = (
    "/lol-gameflow/v1/gameflow-phase",
    "/lol-gameflow/v1/session",
    "/lol-gameflow/v1/gameflow-metadata/player-status",
    "/lol-gameflow/v1/gameflow-metadata/registration-status",
    "/lol-gameflow/v1/extra-game-client-args",
    "/lol-tft/v1/tft",
)

checks = [
    ("Probe presente", PROBE.exists()),
    ("Analyzer presente", ANALYZER.exists()),
    ("Sintaxe probe valida", True),
    ("Sintaxe analyzer valida", True),
    ("Somente localhost", "127.0.0.1" in probe_text),
    ("Somente requests.get", "requests.get(" in probe_text),
    ("Whitelist fixa", "WHITELIST_ENDPOINTS" in probe_text),
    ("Intervalo minimo 5s", "--interval >= 5" in probe_text),
    ("Sem leitura memoria", '"memory_reading": False' in probe_text),
    ("Sem injecao", '"process_injection": False' in probe_text),
    ("Sem input", '"input_automation": False' in probe_text),
]

try:
    if PROBE.exists():
        ast.parse(probe_text, filename=str(PROBE))
except SyntaxError:
    checks[2] = ("Sintaxe probe valida", False)

try:
    if ANALYZER.exists():
        ast.parse(analyzer_text, filename=str(ANALYZER))
except SyntaxError:
    checks[3] = ("Sintaxe analyzer valida", False)

for endpoint in REQUIRED_ENDPOINTS:
    checks.append(
        (
            f"Endpoint presente: {endpoint}",
            endpoint in probe_text,
        )
    )

for item in FORBIDDEN:
    checks.append(
        (
            f"Ausente: {item}",
            item.lower() not in probe_text.lower(),
        )
    )

print("=" * 112)
print("#64 / ROADMAP 25.0H - DIRECTED LIVE STATE PROBE GUARDRAILS")
print("=" * 112)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(
        f"[{i:02d}] {label:<86} "
        f"{'OK' if ok else 'ERRO'}"
    )

print("-" * 112)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#64 ROADMAP 25.0H: DIRECTED PROBE VALIDADO")
