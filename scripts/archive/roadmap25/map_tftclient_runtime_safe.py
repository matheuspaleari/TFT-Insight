from pathlib import Path
import argparse,json,os,re,subprocess,time
from datetime import datetime,timezone
TERMS=("gold","currentgold","xp","experience","round","stage","level","shop","bench","unit","board","health","player","gameplay","tft","economy","income")
SUFFIX={".log",".txt",".json",".yaml",".yml",".cfg",".ini",".xml",".properties"}
MAX=50*1024*1024
def redact(s):
    pats=[
      (r'(?i)(authorization|auth[-_ ]?token|access[-_ ]?token|session[-_ ]?token|playerkey|spectatorkey|authorization-key)\s*[:=]\s*["\']?[^"\',\s]+',r'\1=<REDACTED>'),
      (r'(?i)(-(?:PlayerKey|LeagueClientAuthToken|riotgamesapi-settings|PacketCopMetadata))=("[^"]*"|\S+)',r'\1=<REDACTED>'),
      (r'eyJ[A-Za-z0-9_-]{20,}(?:\.[A-Za-z0-9_-]{20,}){0,2}','<TOKEN_REDACTED>'),
      (r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b','<UUID_REDACTED>'),
      (r'\b(?:\d{1,3}\.){3}\d{1,3}\b','<IP_REDACTED>')]
    for p,r in pats:s=re.sub(p,r,s)
    return s
def procs():
    c='Get-CimInstance Win32_Process -Filter "Name=\'TFTClient.exe\'" | Select ProcessId,Name,ExecutablePath | ConvertTo-Json -Compress'
    try:
      x=subprocess.run(["powershell.exe","-NoProfile","-Command",c],capture_output=True,text=True,timeout=5)
      if not x.stdout.strip():return []
      o=json.loads(x.stdout); return o if isinstance(o,list) else [o]
    except:return []
def snap(roots):
    d={}
    for r in roots:
      if not r.exists():continue
      for dp,dn,fn in os.walk(r):
        dn[:]=[x for x in dn if x not in {"Cache","Code Cache","GPUCache","Crashpad","Crashes"}]
        for n in fn:
          p=Path(dp)/n
          try:
            st=p.stat()
            if p.is_file() and st.st_size<=MAX and (not p.suffix or p.suffix.lower() in SUFFIX):
              d[str(p)]=(st.st_size,st.st_mtime_ns)
          except OSError:pass
    return d
def tail(p):
    try:
      n=p.stat().st_size
      with p.open("rb") as f:
        if n>32768:f.seek(n-32768)
        return redact(f.read(32768).decode("utf8","replace"))
    except:return ""
def main():
    a=argparse.ArgumentParser();a.add_argument("--wait",type=int,default=30);a.add_argument("--output",default="data/tftclient_runtime_mapper");q=a.parse_args()
    roots=[Path(os.getenv("LOCALAPPDATA", "")) / "Riot Games" / "Teamfight Tactics PBE",
           Path(os.getenv("LOCALAPPDATA", "")) / "Riot Games" / "Riot Client" / "Data" / "Sessions",
           Path(os.getenv("PROGRAMDATA",r"C:\ProgramData"))/"Riot Games"/"Metadata"/"teamfighttactics.pbe",
           Path(r"C:\Riot Games\Teamfight Tactics\PBE")]
    ps=procs();print("="*105);print("TFT INSIGHT / 25.0M3 - TFTCLIENT RUNTIME MAPPER");print("="*105)
    print("TFTClient PID:",",".join(str(x.get("ProcessId")) for x in ps) or "NAO LOCALIZADO")
    print("Somente filesystem + listagem de processo; sem memoria/injecao/sniffing/rede/input.")
    s1=snap(roots);print("Snapshot A:",len(s1));time.sleep(q.wait);s2=snap(roots);print("Snapshot B:",len(s2))
    changed=[p for p in s2 if p not in s1 or s2[p]!=s1[p]]
    rows=[]
    for p in changed:
      txt=tail(Path(p)); hits=[]
      for line in txt.splitlines():
        m=sorted({t for t in TERMS if t in line.lower()})
        if m:hits.append({"terms":m,"line":line[:4000]})
      if hits or "tft" in p.lower() or "teamfight" in p.lower():rows.append({"path":p,"hits":hits[:250]})
    ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ");o=Path(q.output);o.mkdir(parents=True,exist_ok=True)
    payload={"captured_at":ts,"tft_processes":ps,"policy":{"filesystem_only":True,"os_process_listing_only":True,"memory_reading":False,"process_injection":False,"packet_sniffing":False,"network_access":False,"input_automation":False,"aggressive_redaction":True},"changed":len(changed),"prioritized":rows}
    (o/f"tftclient_runtime_{ts}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf8")
    lines=["TFT INSIGHT / 25.0M3 - TFTCLIENT RUNTIME MAPPER","="*105,"processes="+json.dumps(ps,ensure_ascii=False),f"changed={len(changed)} prioritized={len(rows)}",""]
    for x in rows:
      lines+=["FILE: "+x["path"]]
      for h in x["hits"]:lines+=["TERMS="+",".join(h["terms"]),h["line"]]
      lines+=["-"*105]
    tp=o/f"tftclient_runtime_{ts}.txt";tp.write_text("\n".join(lines),encoding="utf8");print("TXT:",tp)
if __name__=="__main__":main()
