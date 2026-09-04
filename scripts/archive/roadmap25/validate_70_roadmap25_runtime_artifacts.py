import ast
from pathlib import Path

p = Path(__file__).with_name("discover_tft_runtime_artifacts_safe.py")
t = p.read_text(encoding="utf-8")

checks = [
    ("script presente", p.exists()),
    ("sintaxe", True),
    ("usa filesystem", "os.walk" in t),
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
    "CreateRemoteThread", "VirtualAllocEx", "pymem", "frida",
    "scapy", "pydivert", "requests.get(", "requests.post(",
):
    checks.append((f"ausente {bad}", bad.lower() not in t.lower()))

try:
    if p.exists():
        ast.parse(t)
except SyntaxError:
    checks[1] = ("sintaxe", False)

print("=" * 100)
print("#70 / ROADMAP 25.0M - RUNTIME ARTIFACT DISCOVERY")
print("=" * 100)
for name, ok in checks:
    print(f"{name:<42} {'OK' if ok else 'ERRO'}")
print(f"PASSARAM: {sum(ok for _, ok in checks)}/{len(checks)}")
if not all(ok for _, ok in checks):
    raise SystemExit(1)
print("#70 ROADMAP 25.0M: VALIDADO")
