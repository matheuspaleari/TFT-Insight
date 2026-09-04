import ast
from pathlib import Path

p = Path(__file__).with_name("map_tft_game_process_artifacts_safe.py")
t = p.read_text(encoding="utf-8")

checks = [
    ("script presente", p.exists()),
    ("sintaxe", True),
    ("filesystem", "os.walk" in t),
    ("redaction", "redact_text" in t and "<REDACTED>" in t),
    ("game pid", "gameflow-process-info" in t),
    ("sem requests", "requests" not in t),
    ("sem socket", "socket" not in t),
    ("sem memoria", '"memory_reading": False' in t),
    ("sem injecao", '"process_injection": False' in t),
    ("sem sniffing", '"packet_sniffing": False' in t),
    ("sem input", '"input_automation": False' in t),
    ("sem rede", '"network_access": False' in t),
]

for bad in (
    "OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
    "VirtualAllocEx", "CreateRemoteThread", "pymem",
    "frida", "scapy", "pydivert", "requests.get(",
):
    checks.append((f"ausente {bad}", bad.lower() not in t.lower()))

try:
    if p.exists():
        ast.parse(t)
except SyntaxError:
    checks[1] = ("sintaxe", False)

print("=" * 104)
print("#71 / ROADMAP 25.0M2 - GAME PROCESS ARTIFACT MAPPER")
print("=" * 104)
for name, ok in checks:
    print(f"{name:<44} {'OK' if ok else 'ERRO'}")
print(f"PASSARAM: {sum(ok for _, ok in checks)}/{len(checks)}")
if not all(ok for _, ok in checks):
    raise SystemExit(1)
print("#71 ROADMAP 25.0M2: VALIDADO")
