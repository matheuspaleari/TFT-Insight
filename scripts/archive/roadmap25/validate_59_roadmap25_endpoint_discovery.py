from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/probe_tft_lcu_endpoints_safe.py"

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

checks = [
    ("Probe presente", PROBE.exists()),
    ("Sintaxe valida", True),
    ("Somente localhost", "127.0.0.1" in text),
    ("Somente requests.get", "requests.get(" in text),
    ("Whitelist pequena", "LCU_CANDIDATES" in text),
    ("Endpoint /help", '"/help"' in text),
    ("Gameflow client", '"/lol-gameflow/v1/game-client"' in text),
    ("Gameflow metadata", '"/lol-gameflow/v1/gameflow-metadata/player-status"' in text),
    ("Sem persistencia credencial", '"credential_persistence": False' in text),
]

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

for item in FORBIDDEN:
    checks.append((f"Ausente: {item}", item.lower() not in text.lower()))

print("=" * 100)
print("#59 / ROADMAP 25.0C - SAFE ENDPOINT DISCOVERY GUARDRAILS")
print("=" * 100)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<74} {'OK' if ok else 'ERRO'}")

print("-" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#59 ROADMAP 25.0C: ENDPOINT DISCOVERY VALIDADO")
