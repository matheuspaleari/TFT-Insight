import ast
from pathlib import Path
p=Path(__file__).with_name("map_tftclient_process_environment_safe.py");t=p.read_text(encoding="utf-8")
checks=[("sintaxe",True),("TFTClient","TFTClient.exe" in t),("heartbeat","heartbeat.json" in t),("CIM","Get-CimInstance Win32_Process" in t),("ParentProcessId","ParentProcessId" in t),("redaction","command_line_redaction" in t),("sem memoria","ReadProcessMemory" not in t),("sem injecao","CreateRemoteThread" not in t),("sem sniffing","scapy" not in t and "pydivert" not in t),("sem requests","requests" not in t)]
try:ast.parse(t)
except SyntaxError:checks[0]=("sintaxe",False)
print("#73 / ROADMAP 25.0M4")
for n,x in checks:print(f"{n:<35}", "OK" if x else "ERRO")
print(f"PASSARAM: {sum(x for _,x in checks)}/{len(checks)}")
if not all(x for _,x in checks):raise SystemExit(1)
print("#73 ROADMAP 25.0M4: VALIDADO")
