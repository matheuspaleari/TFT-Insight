import ast
from pathlib import Path
p=Path(__file__).with_name("map_tftclient_runtime_safe.py");t=p.read_text(encoding="utf8")
checks=[("sintaxe",True),("TFTClient","TFTClient.exe" in t),("CIM","Get-CimInstance Win32_Process" in t),("redaction","aggressive_redaction" in t),("sem memoria","ReadProcessMemory" not in t),("sem injecao","CreateRemoteThread" not in t),("sem sniffing","scapy" not in t and "pydivert" not in t),("sem requests","requests" not in t)]
try:ast.parse(t)
except SyntaxError:checks[0]=("sintaxe",False)
print("#72 / ROADMAP 25.0M3")
for n,x in checks:print(f"{n:<30}", "OK" if x else "ERRO")
print(f"PASSARAM: {sum(x for _,x in checks)}/{len(checks)}")
if not all(x for _,x in checks):raise SystemExit(1)
print("#72 ROADMAP 25.0M3: VALIDADO")
