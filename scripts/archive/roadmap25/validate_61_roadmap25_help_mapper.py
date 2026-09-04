from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPER = ROOT / "scripts/map_tft_lcu_help_safe.py"

text = MAPPER.read_text(encoding="utf-8") if MAPPER.exists() else ""

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
    ("Mapper presente", MAPPER.exists()),
    ("Sintaxe valida", True),
    ("Somente localhost", "127.0.0.1" in text),
    ("Consulta somente /help", 'url = f"{base_url}/help"' in text),
    ("Somente requests.get", "requests.get(" in text),
    (
        "Nao executa endpoints descobertos",
        '"discovered_endpoints_executed": False' in text,
    ),
    ("Filtra familia GET", 'method == "GET"' in text),
    ("Credencial nao persiste", '"credential_persistence": False' in text),
    ("Sem leitura de memoria", '"memory_reading": False' in text),
    ("Sem injecao", '"process_injection": False' in text),
    ("Sem input", '"input_automation": False' in text),
]

try:
    if MAPPER.exists():
        ast.parse(text, filename=str(MAPPER))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

for item in FORBIDDEN:
    checks.append((f"Ausente: {item}", item.lower() not in text.lower()))

print("=" * 104)
print("#61 / ROADMAP 25.0E - LCU HELP MAPPER GUARDRAILS")
print("=" * 104)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<78} {'OK' if ok else 'ERRO'}")

print("-" * 104)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#61 ROADMAP 25.0E: /HELP MAPPER VALIDADO")
