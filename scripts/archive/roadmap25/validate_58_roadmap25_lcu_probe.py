from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/probe_tft_lcu_safe.py"

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
    ("Sintaxe Python valida", True),
    ("Localhost fixo", "127.0.0.1" in text),
    ("Somente GET HTTP", "requests.get(" in text),
    ("Lockfile suportado", "lockfile" in text.lower()),
    ("Credencial não persistida", '"credential_persistence": False' in text),
    ("Password redigido", '"password": "<REDACTED>"' in text),
    ("Sem leitura de memoria", '"memory_reading": False' in text),
    ("Sem injecao", '"process_injection": False' in text),
    ("Sem automacao de input", '"input_automation": False' in text),
]

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe Python valida", False)

for item in FORBIDDEN:
    checks.append((f"Ausente: {item}", item.lower() not in text.lower()))

print("=" * 100)
print("#58 / ROADMAP 25.0B - SAFE LCU DISCOVERY GUARDRAILS")
print("=" * 100)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<74} {'OK' if ok else 'ERRO'}")

print("-" * 100)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#58 ROADMAP 25.0B: LCU PROBE HTTP-ONLY VALIDADO")
