import argparse,json,socket
from datetime import datetime,timezone
from pathlib import Path
import requests,urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HOST="127.0.0.1"; PORT=2999
ENDPOINTS=["/swagger/v3/openapi.json","/liveclientdata/activeplayer","/liveclientdata/allgamedata","/liveclientdata/gamestats","/liveclientdata/eventdata"]
def stamp(): return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--timeout",type=float,default=2); a=p.parse_args()
 try:
  with socket.create_connection((HOST,PORT),timeout=a.timeout): opened=True
 except OSError: opened=False
 out={"captured_at":stamp(),"policy":{"localhost_only":True,"official_port_only":True,"get_only":True,"port_scan":False,"memory_reading":False,"process_injection":False,"packet_sniffing":False,"input_automation":False},"port_open":opened,"results":{}}
 print("Porta 2999:", "ABERTA" if opened else "FECHADA")
 if opened:
  for ep in ENDPOINTS:
   try:
    r=requests.get(f"https://{HOST}:{PORT}{ep}",timeout=a.timeout,verify=False,allow_redirects=False)
    try: data=r.json()
    except ValueError: data={"text_preview":r.text[:1000]}
    out["results"][ep]={"status_code":r.status_code,"data":data}
    print(f"[GET] {ep:<45} {r.status_code}")
    if ep.endswith("activeplayer") and isinstance(data,dict):
     for k in ("currentGold","level"): print(f"  {k} = {data.get(k)!r}")
    if ep.endswith("gamestats") and isinstance(data,dict):
     for k in ("gameMode","gameTime"): print(f"  {k} = {data.get(k)!r}")
   except requests.RequestException as e:
    out["results"][ep]={"error":type(e).__name__,"message":str(e)}
 else: print("Nenhum GET feito: a porta oficial 2999 nao esta escutando.")
 d=Path("data/game_client_discovery"); d.mkdir(parents=True,exist_ok=True)
 f=d/f"game_client_discovery_{stamp()}.json"; f.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8"); print("Salvo:",f)
if __name__=="__main__": main()
