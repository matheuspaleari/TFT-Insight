from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPER = ROOT / "scripts/map_tft_lcu_types_safe.py"

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
    ("Somente GET", "requests.get(" in text),
    ("Secao types", 'help_data.get("types")' in text),
    ("Nao chama outros endpoints", '"other_endpoints_called": False' in text),
    ("Sem memoria", '"memory_reading": False' in text),
    ("Sem injecao", '"process_injection": False' in text),
    ("Sem sniffing", '"packet_sniffing": False' in text),
    ("Sem input", '"input_automation": False' in text),
    ("Credencial nao persiste", '"credential_persistence": False' in text),
]

try:
    if MAPPER.exists():
        ast.parse(text, filename=str(MAPPER))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

for item in FORBIDDEN:
    checks.append(
        (f"Ausente: {item}", item.lower() not in text.lower())
    )

print("=" * 110)
print("#67 / ROADMAP 25.0K - LCU TYPE MAPPER GUARDRAILS")
print("=" * 110)

passed = 0

for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(
        f"[{i:02d}] {label:<84} "
        f"{'OK' if ok else 'ERRO'}"
    )

print("-" * 110)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#67 ROADMAP 25.0K: TYPE MAPPER VALIDADO")
