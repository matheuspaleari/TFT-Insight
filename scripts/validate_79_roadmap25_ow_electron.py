from pathlib import Path
p=Path(__file__).parents[1]/"overwolf_poc"/"tft_insight_gep_collector.js"
t=p.read_text(encoding="utf-8")
checks=[
("collector",p.exists()),
("game_info",'"game_info"' in t),
("me",'"me"' in t),
("match_info",'"match_info"' in t),
("store",'"store"' in t),
("board",'"board"' in t),
("bench",'"bench"' in t),
("match_stats",'"match_stats"' in t),
("setRequiredFeatures","setRequiredFeatures(FEATURES)" in t),
("new-info-update","new-info-update" in t),
("new-game-event","new-game-event" in t),
("augments excluido",'"augments"' not in t),
("sem memoria","ReadProcessMemory" not in t),
("sem injecao","CreateRemoteThread" not in t),
("sem sniffing","scapy" not in t.lower() and "pcap" not in t.lower())
]
print("#79 / ROADMAP 25.0R - OW-ELECTRON BOOTSTRAP")
for n,x in checks: print(f"{n:<36}", "OK" if x else "ERRO")
print(f"PASSARAM: {sum(x for _,x in checks)}/{len(checks)}")
if not all(x for _,x in checks): raise SystemExit(1)
print("#79 ROADMAP 25.0R: VALIDADO")
