from __future__ import annotations
import argparse, json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

TARGET = "TFTClient-Win64-Shipping.exe"

def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")

def ps_json(command):
    cp = subprocess.run(
        ["powershell.exe","-NoProfile","-Command",command],
        capture_output=True,text=True,encoding="utf-8",errors="replace",
        timeout=12,check=False
    )
    if cp.returncode != 0 or not cp.stdout.strip():
        return None
    try: return json.loads(cp.stdout)
    except: return None

def as_list(x):
    if x is None: return []
    return x if isinstance(x,list) else [x]

def processes():
    cmd = """Get-CimInstance Win32_Process -Filter "Name='TFTClient-Win64-Shipping.exe'" |
Select-Object ProcessId,ParentProcessId,Name |
ConvertTo-Json -Compress"""
    return as_list(ps_json(cmd))

def tcp(pid):
    cmd = f"""Get-NetTCPConnection -OwningProcess {pid} -ErrorAction SilentlyContinue |
Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess |
ConvertTo-Json -Compress"""
    return as_list(ps_json(cmd))

def udp(pid):
    cmd = f"""Get-NetUDPEndpoint -OwningProcess {pid} -ErrorAction SilentlyContinue |
Select-Object LocalAddress,LocalPort,OwningProcess |
ConvertTo-Json -Compress"""
    return as_list(ps_json(cmd))

def children(pid):
    cmd = f"""Get-CimInstance Win32_Process -Filter "ParentProcessId={pid}" |
Select-Object ProcessId,ParentProcessId,Name |
ConvertTo-Json -Compress"""
    return as_list(ps_json(cmd))

def classify_tcp(x):
    la=str(x.get("LocalAddress",""))
    ra=str(x.get("RemoteAddress",""))
    state=str(x.get("State",""))
    local = la in ("127.0.0.1","::1")
    remote_local = ra in ("127.0.0.1","::1")
    listening = state.lower()=="listen"
    if listening and local: return "LOCALHOST_LISTENER"
    if listening: return "LISTENER"
    if local or remote_local: return "LOCALHOST_CONNECTION"
    return "REMOTE_CONNECTION"

def redact_remote(x):
    # Keep ports and localhost addresses; redact external IP addresses.
    y=dict(x)
    for k in ("LocalAddress","RemoteAddress"):
        v=str(y.get(k,""))
        if v and v not in ("127.0.0.1","::1","0.0.0.0","::") and re.fullmatch(r"[0-9a-fA-F:.]+",v):
            y[k]="<REMOTE_ADDRESS>"
    return y

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="data/shipping_runtime_surface")
    a=ap.parse_args()

    procs=processes()
    report=[]
    for p in procs:
        pid=int(p["ProcessId"])
        tc=tcp(pid); ud=udp(pid); ch=children(pid)
        tcp_rows=[]
        for x in tc:
            safe=redact_remote(x)
            safe["classification"]=classify_tcp(x)
            tcp_rows.append(safe)
        report.append({
            "process":p,
            "tcp":tcp_rows,
            "udp":[redact_remote(x) for x in ud],
            "children":ch,
        })

    od=Path(a.output);od.mkdir(parents=True,exist_ok=True);ts=stamp()
    payload={
        "captured_at":ts,
        "target":TARGET,
        "policy":{
            "os_metadata_only":True,
            "network_traffic_capture":False,
            "packet_sniffing":False,
            "memory_reading":False,
            "process_injection":False,
            "endpoint_requests":False,
            "input_automation":False,
            "external_addresses_redacted":True
        },
        "report":report
    }
    jp=od/f"shipping_surface_{ts}.json"
    tp=od/f"shipping_surface_{ts}.txt"
    jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

    lines=[
        "TFT INSIGHT / ROADMAP 25.0N - SHIPPING RUNTIME SURFACE MAPPER",
        "="*108,
        f"target={TARGET}",
        f"processes={len(procs)}",""
    ]
    for r in report:
        p=r["process"]
        lines += [
            f"PROCESS pid={p.get('ProcessId')} parent={p.get('ParentProcessId')} name={p.get('Name')}",
            "TCP:"
        ]
        if not r["tcp"]: lines.append("  <none>")
        for x in r["tcp"]:
            lines.append("  "+json.dumps(x,ensure_ascii=False))
        lines.append("UDP:")
        if not r["udp"]: lines.append("  <none>")
        for x in r["udp"]:
            lines.append("  "+json.dumps(x,ensure_ascii=False))
        lines.append("CHILDREN:")
        if not r["children"]: lines.append("  <none>")
        for x in r["children"]:
            lines.append("  "+json.dumps(x,ensure_ascii=False))
        lines.append("-"*108)

    tp.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print("="*108)
    print("TFT INSIGHT / ROADMAP 25.0N - SHIPPING RUNTIME SURFACE MAPPER")
    print("="*108)
    print("Shipping PIDs:",", ".join(str(x.get("ProcessId")) for x in procs) or "NAO ENCONTRADO")
    listeners=sum(1 for r in report for x in r["tcp"] if "LISTENER" in x["classification"])
    localhost=sum(1 for r in report for x in r["tcp"] if x["classification"]=="LOCALHOST_LISTENER")
    print("TCP listeners       :",listeners)
    print("Localhost listeners :",localhost)
    print("TXT:",tp)
    print("Envie o TXT.")
if __name__=="__main__":
    main()
