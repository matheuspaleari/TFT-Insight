from pathlib import Path
import argparse,json,os,re,subprocess
from datetime import datetime,timezone

HBROOT=Path(os.environ.get("LOCALAPPDATA", ""))/"Riot Games"/"Riot Client"/"Data"/"Sessions"

def stamp(): return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")

def redact(s):
    if s is None:return None
    for p,r in [
      (r'(?i)(authorization|auth[-_ ]?token|access[-_ ]?token|session[-_ ]?token|playerkey|spectatorkey|authorization-key)\\s*[:=]\\s*["\\\']?[^"\\\',\\s]+',r'\\1=<REDACTED>'),
      (r'(?i)(--?[A-Za-z0-9_-]*(?:token|key|auth)[A-Za-z0-9_-]*)=("[^"]*"|\\S+)',r'\\1=<REDACTED>'),
      (r'eyJ[A-Za-z0-9_-]{20,}(?:\\.[A-Za-z0-9_-]{20,}){0,2}','<TOKEN_REDACTED>')]:
        s=re.sub(p,r,s)
    return s

def ps(command):
    x=subprocess.run(["powershell.exe","-NoProfile","-Command",command],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=10)
    if x.returncode or not x.stdout.strip():return None
    try:return json.loads(x.stdout)
    except:return None

def proc(pid):
    return ps('Get-CimInstance Win32_Process -Filter "ProcessId=%d" | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress' % pid)

def tfts():
    o=ps('Get-CimInstance Win32_Process -Filter "Name=\\\'TFTClient.exe\\\'" | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress')
    if o is None:return []
    return o if isinstance(o,list) else [o]

def heartbeat():
    if not HBROOT.exists():return None
    try: fs=sorted(HBROOT.rglob("*.heartbeat.json"),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    except:return None
    for p in fs[:50]:
        try:d=json.loads(p.read_text(encoding="utf-8",errors="replace"))
        except:continue
        src=d.get("source",{}); dat=d.get("data",{})
        if str(src.get("productId","")).lower()=="teamfighttactics":
            return {"path":str(p),"phase":dat.get("phase"),"pid":src.get("pid"),"productId":src.get("productId"),"patchlineId":src.get("patchlineId")}
    return None

def safe(p):
    if not isinstance(p,dict):return p
    return {"ProcessId":p.get("ProcessId"),"ParentProcessId":p.get("ParentProcessId"),"Name":p.get("Name"),"ExecutablePath":redact(p.get("ExecutablePath")),"CommandLine":redact(p.get("CommandLine"))}

def chain(pid):
    a=[];seen=set()
    for _ in range(8):
        if not pid or pid in seen:break
        seen.add(pid);p=proc(pid)
        if not isinstance(p,dict):break
        a.append(safe(p))
        try:pid=int(p.get("ParentProcessId") or 0)
        except:break
    return a

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="data/tftclient_process_environment");a=ap.parse_args()
    hb=heartbeat();hpid=int(hb["pid"]) if hb and hb.get("pid") else None
    hp=proc(hpid) if hpid else None; ts=tfts()
    data={"captured_at":stamp(),"policy":{"os_process_metadata_only":True,"filesystem_heartbeat_read_only":True,"memory_reading":False,"process_injection":False,"packet_sniffing":False,"network_access":False,"input_automation":False,"command_line_redaction":True},"heartbeat":hb,"heartbeat_process":safe(hp),"heartbeat_parent_chain":chain(hpid) if hpid else [],"tftclient_processes":[{"process":safe(x),"parent_chain":chain(int(x["ProcessId"]))} for x in ts if x.get("ProcessId")]}
    od=Path(a.output);od.mkdir(parents=True,exist_ok=True);st=stamp()
    jp=od/f"process_environment_{st}.json";tp=od/f"process_environment_{st}.txt"
    jp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["TFT INSIGHT / ROADMAP 25.0M4 - TFTCLIENT PROCESS ENVIRONMENT MAPPER","="*110,"heartbeat="+json.dumps(hb,ensure_ascii=False),"","HEARTBEAT PROCESS",json.dumps(safe(hp),ensure_ascii=False,indent=2),"","HEARTBEAT PARENT CHAIN"]
    lines += [json.dumps(x,ensure_ascii=False) for x in data["heartbeat_parent_chain"]]
    lines += ["","TFTCLIENT PROCESSES",json.dumps(data["tftclient_processes"],ensure_ascii=False,indent=2)]
    tp.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("="*110);print("TFT INSIGHT / ROADMAP 25.0M4");print("="*110)
    print("Heartbeat PID:",hpid or "NAO ENCONTRADO");print("TFTClient PIDs:",",".join(str(x.get("ProcessId")) for x in ts) or "NAO ENCONTRADO")
    print("TXT:",tp);print("Envie o TXT.")
if __name__=="__main__":main()
