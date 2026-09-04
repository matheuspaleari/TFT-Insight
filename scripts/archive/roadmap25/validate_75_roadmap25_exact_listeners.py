import ast
from pathlib import Path
p=Path(__file__).with_name("verify_tft_exact_listeners_safe.py")
t=p.read_text(encoding="utf-8")
checks=[
("sintaxe",True),
("TFTClient","TFTClient.exe" in t),
("Shipping","TFTClient-Win64-Shipping.exe" in t),
("netstat TCP",'["netstat","-ano","-p",proto]' in t),
("Get-NetTCPConnection","Get-NetTCPConnection" in t),
("Get-NetUDPEndpoint","Get-NetUDPEndpoint" in t),
("sem sniffing",'"packet_sniffing":False' in t),
("sem captura",'"packet_capture":False' in t),
("sem memoria",'"memory_reading":False' in t),
("sem injecao",'"process_injection":False' in t),
("sem requests",'"endpoint_requests":False' in t),
("sem input",'"input_automation":False' in t),
]
for bad in ("OpenProcess","ReadProcessMemory","WriteProcessMemory","VirtualAllocEx","CreateRemoteThread","pymem","frida","scapy","pydivert","requests.get(","requests.post("):
    checks.append(("ausente "+bad,bad.lower() not in t.lower()))
try: ast.parse(t)
except SyntaxError: checks[0]=("sintaxe",False)
print("#75 / ROADMAP 25.0N2")
for n,x in checks: print(f"{n:<40}", "OK" if x else "ERRO")
print(f"PASSARAM: {sum(x for _,x in checks)}/{len(checks)}")
if not all(x for _,x in checks): raise SystemExit(1)
print("#75 ROADMAP 25.0N2: VALIDADO")
