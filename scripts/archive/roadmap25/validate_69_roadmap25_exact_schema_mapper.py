import ast
from pathlib import Path

p = Path(__file__).with_name("map_tft_lcu_exact_schema_safe.py")
t = p.read_text(encoding="utf-8")

checks = [
    ("script presente", p.exists()),
    ("sintaxe", True),
    ("GET /help", 'base + "/help"' in t and "requests.get(" in t),
    ("matching exato", "exact_type_mentions" in t and "v == target" in t),
    ("functions separado", 'section(help_data, "functions")' in t),
    ("events separado", 'section(help_data, "events")' in t),
    ("types separado", 'section(help_data, "types")' in t),
    ("TFT GameData", "LolTftGameflowGameData" in t),
    ("TFT Session", "LolTftGameflowSession" in t),
    ("GameStateUpdate", "LolGameflowGameStateUpdate" in t),
    ("currentGold", "currentGold" in t),
    ("xp", '"xp"' in t),
    ("round", '"round"' in t),
    ("stage", '"stage"' in t),
    ("nao executa endpoints", '"discovered_endpoints_executed": False' in t),
    ("sem memoria", '"memory_reading": False' in t),
    ("sem injecao", '"process_injection": False' in t),
    ("sem sniffing", '"packet_sniffing": False' in t),
    ("sem input", '"input_automation": False' in t),
]

for bad in (
    "OpenProcess", "ReadProcessMemory", "WriteProcessMemory",
    "CreateRemoteThread", "VirtualAllocEx", "pymem", "frida",
    "scapy", "pydivert", "requests.post(", "requests.put(",
    "requests.patch(", "requests.delete(",
):
    checks.append((f"ausente {bad}", bad.lower() not in t.lower()))

try:
    if p.exists():
        ast.parse(t)
except SyntaxError:
    checks[1] = ("sintaxe", False)

print("=" * 100)
print("#69 / ROADMAP 25.0L2 - EXACT API SCHEMA MAPPER")
print("=" * 100)
for name, ok in checks:
    print(f"{name:<45} {'OK' if ok else 'ERRO'}")
print(f"PASSARAM: {sum(ok for _, ok in checks)}/{len(checks)}")
if not all(ok for _, ok in checks):
    raise SystemExit(1)
print("#69 ROADMAP 25.0L2: VALIDADO")
