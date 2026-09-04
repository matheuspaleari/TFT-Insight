import ast
from pathlib import Path
p = Path(__file__).with_name("cross_map_tft_lcu_types_safe.py")
t = p.read_text(encoding="utf-8")
checks = [
 ("sintaxe", True),
 ("GET /help", 'base + "/help"' in t and "requests.get(" in t),
 ("target TFT gameflow", "LolTftGameflowSession" in t),
 ("game state", "LolGameflowGameStateUpdate" in t),
 ("gold", "currentGold" in t),
 ("xp", '"xp"' in t),
 ("round", '"round"' in t),
 ("stage", '"stage"' in t),
 ("sem executar descobertos", '"discovered_endpoints_executed": False' in t),
 ("sem memoria", '"memory_reading": False' in t),
 ("sem injecao", '"process_injection": False' in t),
 ("sem sniffing", '"packet_sniffing": False' in t),
 ("sem input", '"input_automation": False' in t),
]
for bad in ("OpenProcess","ReadProcessMemory","WriteProcessMemory","CreateRemoteThread",
            "requests.post(","requests.put(","requests.patch(","requests.delete(","scapy","pydivert","frida","pymem"):
    checks.append((f"ausente {bad}", bad.lower() not in t.lower()))
try: ast.parse(t)
except SyntaxError: checks[0] = ("sintaxe", False)
print("#68 / ROADMAP 25.0L")
for n, ok in checks: print(f"{n:<38}", "OK" if ok else "ERRO")
print(f"PASSARAM: {sum(ok for _,ok in checks)}/{len(checks)}")
if not all(ok for _,ok in checks): raise SystemExit(1)
print("#68 ROADMAP 25.0L: VALIDADO")
