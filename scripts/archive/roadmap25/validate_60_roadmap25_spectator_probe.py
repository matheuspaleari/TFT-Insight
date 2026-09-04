from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/probe_tft_spectator_safe.py"

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
    "pbe1",
)

checks = [
    ("Probe presente", PROBE.exists()),
    ("Sintaxe valida", True),
    ("Somente requests.get", "requests.get(" in text),
    ("Endpoint spectator-tft-v5 correto",
     "/lol/spectator/tft/v5/active-games/by-puuid/" in text),
    ("Account-v1 por Riot ID",
     "/riot/account/v1/accounts/by-riot-id/" in text),
    ("Chave lida de RIOT_API_KEY", 'os.getenv("RIOT_API_KEY"' in text),
    ("Chave nao persistida", '"api_key_persisted": False' in text),
    ("Platforms documentadas possuem BR1", '"br1"' in text),
    ("Sem rota PBE inventada", "Nao vamos adivinhar rotas como PBE1." in text),
]

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

for item in FORBIDDEN:
    checks.append((f"Ausente: {item}", item.lower() not in text.lower()))

print("=" * 104)
print("#60 / ROADMAP 25.0D - SAFE SPECTATOR PROBE GUARDRAILS")
print("=" * 104)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<78} {'OK' if ok else 'ERRO'}")

print("-" * 104)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#60 ROADMAP 25.0D: SPECTATOR PROBE OFICIAL VALIDADO")
