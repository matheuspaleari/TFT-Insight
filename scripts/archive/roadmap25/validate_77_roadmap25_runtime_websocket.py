import ast
from pathlib import Path
p=Path(__file__).with_name("map_tft_runtime_websocket_evidence_safe.py")
t=p.read_text(encoding="utf-8")
checks=[
("sintaxe",True),("websocket","websocket" in t.lower()),("stomp","stomp" in t.lower()),
("xmpp","xmpp" in t.lower()),("offline",'"offline_static_text_only":True' in t),
("sem rede",'"network_access":False' in t),("sem endpoint",'"endpoint_execution":False' in t),
("sem binario",'"binary_inspection":False' in t),("sem memoria",'"memory_reading":False' in t),
("sem sniffing",'"packet_sniffing":False' in t),("sem injecao",'"process_injection":False' in t),
("sem input",'"input_automation":False' in t)]
for bad in ("OpenProcess","ReadProcessMemory","WriteProcessMemory","scapy","pydivert","frida","pymem","requests.get(","requests.post(","socket.socket"):
    checks.append(("ausente "+bad,bad.lower() not in t.lower()))
try: ast.parse(t)
except SyntaxError: checks[0]=("sintaxe",False)
print("#77 / ROADMAP 25.0P")
for n,x in checks: print(f"{n:<40}", "OK" if x else "ERRO")
print(f"PASSARAM: {sum(x for _,x in checks)}/{len(checks)}")
if not all(x for _,x in checks): raise SystemExit(1)
print("#77 ROADMAP 25.0P: VALIDADO")
