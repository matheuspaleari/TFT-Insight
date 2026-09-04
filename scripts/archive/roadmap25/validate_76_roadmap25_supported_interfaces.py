import ast
from pathlib import Path

p = Path(__file__).with_name("discover_tft_supported_runtime_interfaces_safe.py")
t = p.read_text(encoding="utf-8")

checks = [
    ("script presente", p.exists()),
    ("sintaxe", True),
    ("offline static text", '"offline_static_text_only": True' in t),
    ("sem binarios", '"binary_inspection": False' in t),
    ("sem memoria", '"memory_reading": False' in t),
    ("sem rede", '"network_access": False' in t),
    ("sem endpoints", '"endpoint_execution": False' in t),
    ("sem sniffing", '"packet_sniffing": False' in t),
    ("sem injecao", '"process_injection": False' in t),
    ("sem input", '"input_automation": False' in t),
    ("redaction", '"redaction_enabled": True' in t),
    ("procura schemas", '"swagger"' in t and '"openapi"' in t and '"schema"' in t),
    ("procura gameplay", '"gold"' in t and '"round"' in t and '"shop"' in t),
]

for bad in (
    "OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
    "VirtualAllocEx", "CreateRemoteThread", "pymem", "frida",
    "scapy", "pydivert", "requests.get(", "requests.post(",
    "urllib.request", "socket.socket",
):
    checks.append((f"ausente {bad}", bad.lower() not in t.lower()))

try:
    if p.exists():
        ast.parse(t)
except SyntaxError:
    checks[1] = ("sintaxe", False)

print("=" * 104)
print("#76 / ROADMAP 25.0O - SUPPORTED RUNTIME INTERFACE DISCOVERY")
print("=" * 104)
for name, ok in checks:
    print(f"{name:<46} {'OK' if ok else 'ERRO'}")
print(f"PASSARAM: {sum(ok for _, ok in checks)}/{len(checks)}")
if not all(ok for _, ok in checks):
    raise SystemExit(1)
print("#76 ROADMAP 25.0O: VALIDADO")
