import ast
from pathlib import Path
p=Path(__file__).with_name("probe_tft_game_client_2999_safe.py")
t=p.read_text(encoding="utf-8")
checks=[("sintaxe",True),("localhost",'HOST="127.0.0.1"' in t),("porta 2999","PORT=2999" in t),("GET","requests.get(" in t),("sem memoria",'"memory_reading":False' in t),("sem injecao",'"process_injection":False' in t),("sem sniffing",'"packet_sniffing":False' in t),("sem input",'"input_automation":False' in t)]
try: ast.parse(t)
except SyntaxError: checks[0]=("sintaxe",False)
print("#65 ROADMAP 25.0I")
for n,o in checks: print(f"{n:<20}", "OK" if o else "ERRO")
if not all(o for _,o in checks): raise SystemExit(1)
print("#65: VALIDADO")
