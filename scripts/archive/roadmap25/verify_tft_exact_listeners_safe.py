from __future__ import annotations
import argparse, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

TARGETS = ("TFTClient.exe", "TFTClient-Win64-Shipping.exe")

def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")

def run_json(command):
    cp = subprocess.run(
        ["powershell.exe","-NoProfile","-Command",command],
        capture_output=True,text=True,encoding="utf-8",errors="replace",
        timeout=12,check=False
    )
    if cp.returncode != 0 or not cp.stdout.strip():
        return None
    try:
        return json.loads(cp.stdout)
    except Exception:
        return None

def as_list(x):
    if x is None:
        return []
    return x if isinstance(x,list) else [x]

def get_processes():
    cmd = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -eq 'TFTClient.exe' -or $_.Name -eq 'TFTClient-Win64-Shipping.exe' } | "
        "Select-Object ProcessId,ParentProcessId,Name | ConvertTo-Json -Compress"
    )
    return as_list(run_json(cmd))

def get_net_tcp(pid):
    cmd = (
        f"Get-NetTCPConnection -OwningProcess {pid} -ErrorAction SilentlyContinue | "
        "ForEach-Object { "
        "[PSCustomObject]@{LocalAddress=$_.LocalAddress;LocalPort=$_.LocalPort;"
        "RemoteAddress=$_.RemoteAddress;RemotePort=$_.RemotePort;"
        "State=$_.State.ToString();OwningProcess=$_.OwningProcess} } | "
        "ConvertTo-Json -Compress"
    )
    return as_list(run_json(cmd))

def get_net_udp(pid):
    cmd = (
        f"Get-NetUDPEndpoint -OwningProcess {pid} -ErrorAction SilentlyContinue | "
        "Select-Object LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Compress"
    )
    return as_list(run_json(cmd))

def netstat(proto):
    cp = subprocess.run(
        ["netstat","-ano","-p",proto],
        capture_output=True,text=True,encoding="utf-8",errors="replace",
        timeout=10,check=False
    )
    rows=[]
    for line in cp.stdout.splitlines():
        parts=line.split()
        if not parts:
            continue
        if proto=="tcp":
            if len(parts) < 5 or parts[0].upper()!="TCP":
                continue
            try: pid=int(parts[4])
            except: continue
            rows.append({"local":parts[1],"remote":parts[2],"state":parts[3].upper(),"pid":pid})
        else:
            if len(parts) < 4 or parts[0].upper()!="UDP":
                continue
            try: pid=int(parts[-1])
            except: continue
            rows.append({"local":parts[1],"remote":parts[2],"pid":pid})
    return rows

def is_loopback(ep):
    host=ep
    if ep.startswith("["):
        host=ep.split("]")[0].strip("[")
    elif ":" in ep:
        host=ep.rsplit(":",1)[0]
    return host in ("127.0.0.1","::1")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="data/exact_listener_verifier")
    a=ap.parse_args()

    procs=get_processes()
    ns_tcp=netstat("tcp")
    ns_udp=netstat("udp")
    report=[]

    for p in procs:
        pid=int(p["ProcessId"])
        tcp_rows=[x for x in ns_tcp if x["pid"]==pid]
        udp_rows=[x for x in ns_udp if x["pid"]==pid]
        listeners=[x for x in tcp_rows if x["state"]=="LISTENING"]
        localhost=[x for x in listeners if is_loopback(x["local"])]
        report.append({
            "process":p,
            "summary":{
                "tcp_rows":len(tcp_rows),
                "tcp_listening":len(listeners),
                "localhost_listening":len(localhost),
                "udp_rows":len(udp_rows),
            },
            "listeners":listeners,
            "localhost_listeners":localhost,
            "get_net_tcp":get_net_tcp(pid),
            "get_net_udp":get_net_udp(pid),
            "netstat_udp":udp_rows,
        })

    od=Path(a.output);od.mkdir(parents=True,exist_ok=True);ts=stamp()
    payload={
        "captured_at":ts,
        "policy":{
            "os_network_metadata_only":True,
            "packet_capture":False,
            "packet_sniffing":False,
            "memory_reading":False,
            "process_injection":False,
            "endpoint_requests":False,
            "input_automation":False,
        },
        "targets":list(TARGETS),
        "report":report,
    }
    jp=od/f"exact_listeners_{ts}.json"
    tp=od/f"exact_listeners_{ts}.txt"
    jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

    lines=["TFT INSIGHT / ROADMAP 25.0N2 - EXACT LISTENER VERIFIER","="*110,""]
    for item in report:
        p=item["process"];s=item["summary"]
        lines += [
            f"PROCESS {p.get('Name')} PID={p.get('ProcessId')} PARENT={p.get('ParentProcessId')}",
            f"tcp_rows={s['tcp_rows']}",
            f"tcp_listening={s['tcp_listening']}",
            f"localhost_listening={s['localhost_listening']}",
            f"udp_rows={s['udp_rows']}",
            "LISTENERS:"
        ]
        lines += ["  <none>"] if not item["listeners"] else ["  "+json.dumps(x,ensure_ascii=False) for x in item["listeners"]]
        lines.append("LOCALHOST LISTENERS:")
        lines += ["  <none>"] if not item["localhost_listeners"] else ["  "+json.dumps(x,ensure_ascii=False) for x in item["localhost_listeners"]]
        lines.append("GET-NETTCP:")
        lines += ["  <none>"] if not item["get_net_tcp"] else ["  "+json.dumps(x,ensure_ascii=False) for x in item["get_net_tcp"]]
        lines.append("NETSTAT UDP:")
        lines += ["  <none>"] if not item["netstat_udp"] else ["  "+json.dumps(x,ensure_ascii=False) for x in item["netstat_udp"]]
        lines.append("-"*110)
    tp.write_text("\n".join(lines)+"\n",encoding="utf-8")

    print("="*110)
    print("TFT INSIGHT / ROADMAP 25.0N2 - EXACT LISTENER VERIFIER")
    print("="*110)
    if not report:
        print("Nenhum processo alvo encontrado.")
    for item in report:
        p=item["process"];s=item["summary"]
        print(f"{p.get('Name')} PID={p.get('ProcessId')} | LISTENING={s['tcp_listening']} | LOCALHOST={s['localhost_listening']} | UDP={s['udp_rows']}")
    print("TXT:",tp)
    print("Envie o TXT.")
if __name__=="__main__":
    main()
