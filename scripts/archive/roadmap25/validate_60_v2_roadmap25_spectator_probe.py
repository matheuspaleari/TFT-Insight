from __future__ import annotations

import ast
import re
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
)

checks = [
    ("Probe presente", PROBE.exists()),
    ("Sintaxe valida", True),
    ("Somente requests.get", "requests.get(" in text),
    (
        "Endpoint spectator-tft-v5 correto",
        "/lol/spectator/tft/v5/active-games/by-puuid/" in text,
    ),
    (
        "Account-v1 por Riot ID",
        "/riot/account/v1/accounts/by-riot-id/" in text,
    ),
    (
        "Chave lida de RIOT_API_KEY",
        'os.getenv("RIOT_API_KEY"' in text,
    ),
    (
        "Chave nao persistida",
        '"api_key_persisted": False' in text,
    ),
    (
        "Platforms documentadas possuem BR1",
        '"br1"' in text,
    ),
]

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

for item in FORBIDDEN:
    checks.append(
        (
            f"Ausente: {item}",
            item.lower() not in text.lower(),
        )
    )

# Não bloqueia texto explicativo contendo "PBE1".
# Bloqueia apenas se PBE1 aparecer como valor real de rota/plataforma.
pbe_route_patterns = (
    r'["\']pbe1["\']\s*,',
    r'platform\s*=\s*["\']pbe1["\']',
    r'--platform\s+pbe1',
    r'https://pbe1\.api\.riotgames\.com',
)

pbe_route_used = any(
    re.search(pattern, text, flags=re.IGNORECASE)
    for pattern in pbe_route_patterns
)

checks.append(
    (
        "Rota PBE1 nao e usada como platform real",
        not pbe_route_used,
    )
)

print("=" * 104)
print("#60-V2 / ROADMAP 25.0D - SAFE SPECTATOR PROBE GUARDRAILS")
print("=" * 104)

passed = 0

for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(
        f"[{i:02d}] "
        f"{label:<78} "
        f"{'OK' if ok else 'ERRO'}"
    )

print("-" * 104)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#60-V2 ROADMAP 25.0D: SPECTATOR PROBE OFICIAL VALIDADO")
