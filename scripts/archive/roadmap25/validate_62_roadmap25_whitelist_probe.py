from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/probe_tft_lcu_whitelist_safe.py"

text = PROBE.read_text(encoding="utf-8") if PROBE.exists() else ""

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
    "/lol-pre-end-of-game/v1/currentSequenceEvent",
    "/lol-end-of-game/v1/tft-eog-stats",
)

checks = [
    ("Probe presente", PROBE.exists()),
    ("Sintaxe valida", True),
    ("Somente localhost", "127.0.0.1" in text),
    ("Somente requests.get", "requests.get(" in text),
    ("Whitelist fixa", "WHITELIST_ENDPOINTS" in text),
    ("Credencial nao persiste", '"credential_persistence": False' in text),
    ("Sem leitura de memoria", '"memory_reading": False' in text),
    ("Sem injecao", '"process_injection": False' in text),
    ("Sem input", '"input_automation": False' in text),
]

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

for endpoint in REQUIRED_ENDPOINTS:
    checks.append((f"Endpoint presente: {endpoint}", endpoint in text))

for item in FORBIDDEN:
    checks.append((f"Ausente: {item}", item.lower() not in text.lower()))

print("=" * 108)
print("#62 / ROADMAP 25.0F - LCU WHITELIST PROBE GUARDRAILS")
print("=" * 108)

passed = 0

for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(
        f"[{i:02d}] "
        f"{label:<82} "
        f"{'OK' if ok else 'ERRO'}"
    )

print("-" * 108)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#62 ROADMAP 25.0F: WHITELIST PROBE VALIDADO")
