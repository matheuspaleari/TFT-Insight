import ast
from pathlib import Path
p=Path(__file__).with_name("map_tft_shipping_runtime_surface_safe.py")
t=p.read_text(encoding="utf-8")
checks=[
("sintaxe",True),
("Shipping target","TFTClient-Win64-Shipping.exe" in t),
("TCP metadata","Get-NetTCPConnection" in t),
("UDP metadata","Get-NetUDPEndpoint" in t),
("process children","ParentProcessId" in t),
("external redaction","external_addresses_redacted" in t),
("sem sniffing",'"packet_sniffing":False' in t),
("sem captura",'"network_traffic_capture":False' in t),
("sem memoria",'"memory_reading":False' in t),
("sem injecao",'"process_injection":False' in t),
("sem requests",'"endpoint_requests":False' in t),
("sem input",'"input_automation":False' in t),
]
for bad in ("ReadProcessMemory","WriteProcessMemory","OpenProcess","CreateRemoteThread","VirtualAllocEx","scapy","pydivert","frida","pymem","requests.get(","requests.post("):
    checks.append(("ausente "+bad,bad.lower() not in t.lower()))
try: ast.parse(t)
except SyntaxError: checks[0]=("sintaxe",False)
print("#74 / ROADMAP 25.0N - SHIPPING RUNTIME SURFACE")
for n,x in checks: print(f"{n:<40}", "OK" if x else "ERRO")
print(f"PASSARAM: {sum(x for _,x in checks)}/{len(checks)}")
if not all(x for _,x in checks): raise SystemExit(1)
print("#74 ROADMAP 25.0N: VALIDADO")
