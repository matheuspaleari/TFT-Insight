from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/probe_tft_live_client_safe.py"

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
)

checks = [
    ("Probe presente", PROBE.exists()),
    ("Sintaxe Python valida", True),
    ("Host fixo em 127.0.0.1", 'HOST = "127.0.0.1"' in text),
    ("Porta fixa 2999", "PORT = 2999" in text),
    ("Somente requests.get", "requests.get(" in text and "requests.post(" not in text),
    ("Endpoint OpenAPI", "/swagger/v3/openapi.json" in text),
    ("Endpoint allgamedata", "/liveclientdata/allgamedata" in text),
    ("Flag sem leitura de memoria", '"memory_reading": False' in text),
    ("Flag sem injecao", '"process_injection": False' in text),
    ("Flag sem automacao de input", '"input_automation": False' in text),
]

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe Python valida", False)

for forbidden in FORBIDDEN:
    checks.append((f"Ausente: {forbidden}", forbidden.lower() not in text.lower()))

print("=" * 96)
print("#57 / ROADMAP 25.0A - SAFE LIVE PROBE GUARDRAILS")
print("=" * 96)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<70} {'OK' if ok else 'ERRO'}")

print("-" * 96)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#57 ROADMAP 25.0A: PROBE HTTP-ONLY VALIDADO")
