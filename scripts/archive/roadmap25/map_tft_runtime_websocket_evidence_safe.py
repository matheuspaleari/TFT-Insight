from __future__ import annotations
import argparse, json, os, re
from datetime import datetime, timezone
from pathlib import Path

ROOTS = (
    Path(r"C:\Riot Games\Teamfight Tactics\PBE"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Riot Games" / "Teamfight Tactics PBE",
)
SUFFIXES={".ini",".cfg",".json",".yaml",".yml",".xml",".properties",".txt",".log"}
TERMS=("websocket","websockets","ws://","wss://","stomp","xmpp","endpoint","host","url","uri",
       "service","plugin","rpc","grpc","localhost","127.0.0.1","tft","teamfighttactics")
CONTEXT=4
MAX_SIZE=8*1024*1024
SKIP={".git","__pycache__","Cache","Code Cache","GPUCache","Crashpad","Crashes"}

TOKEN_PATTERNS=[
    re.compile(r'(?i)(authorization|access[_ -]?token|auth[_ -]?token|session[_ -]?token)\s*[:=]\s*["\']?[^"\',\s]+'),
    re.compile(r'eyJ[A-Za-z0-9_-]{20,}(?:\.[A-Za-z0-9_-]{20,}){0,2}')
]

def ts(): return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
def redact(s):
    for p in TOKEN_PATTERNS:
        s=p.sub("<REDACTED>",s)
    return s

def scan(path):
    try:
        if path.stat().st_size > MAX_SIZE: return []
        lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    except OSError: return []
    hitlines=[]
    for i,line in enumerate(lines):
        low=line.lower()
        matched=sorted({x for x in TERMS if x in low})
        if matched: hitlines.append((i,matched))
    groups=[]
    seen=set()
    for i,matched in hitlines:
        lo=max(0,i-CONTEXT); hi=min(len(lines),i+CONTEXT+1)
        key=(lo,hi)
        if key in seen: continue
        seen.add(key)
        context=[{"line":n+1,"text":redact(lines[n])[:2500]} for n in range(lo,hi)]
        blob="\n".join(x["text"].lower() for x in context)
        score=0
        if "ws://" in blob or "wss://" in blob: score+=8
        if "websocket" in blob: score+=5
        if "stomp" in blob or "xmpp" in blob: score+=3
        if "localhost" in blob or "127.0.0.1" in blob: score+=5
        if "tft" in blob or "teamfighttactics" in blob: score+=4
        if "endpoint" in blob or "service" in blob or "plugin" in blob: score+=2
        groups.append({"score":score,"matched":matched,"context":context})
    return groups

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="data/runtime_websocket_evidence")
    a=ap.parse_args()
    results=[]; scanned=0
    for root in ROOTS:
        if not root.exists(): continue
        for dp,dns,fns in os.walk(root):
            dns[:]=[d for d in dns if d not in SKIP]
            for fn in fns:
                p=Path(dp)/fn
                if p.suffix.lower() not in SUFFIXES: continue
                scanned+=1
                groups=scan(p)
                if groups:
                    results.append({"path":str(p),"groups":groups,
                                    "max_score":max(x["score"] for x in groups)})
    results.sort(key=lambda x:(-x["max_score"],x["path"].lower()))
    od=Path(a.output); od.mkdir(parents=True,exist_ok=True); stamp=ts()
    payload={"captured_at":stamp,
      "policy":{"offline_static_text_only":True,"network_access":False,
      "endpoint_execution":False,"binary_inspection":False,"memory_reading":False,
      "packet_sniffing":False,"process_injection":False,"input_automation":False},
      "scanned_files":scanned,"matched_files":len(results),"results":results}
    jp=od/f"runtime_websocket_evidence_{stamp}.json"
    tp=od/f"runtime_websocket_evidence_{stamp}.txt"
    jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    out=["TFT INSIGHT / ROADMAP 25.0P - RUNTIME CONFIG & WEBSOCKET EVIDENCE MAPPER","="*112,
         f"scanned_files={scanned}",f"matched_files={len(results)}",""]
    for r in results[:80]:
        out.append(f"MAX_SCORE={r['max_score']} FILE={r['path']}")
        for g in sorted(r["groups"],key=lambda x:-x["score"]):
            out.append(f"  SCORE={g['score']} TERMS={','.join(g['matched'])}")
            for c in g["context"]: out.append(f"    L{c['line']}: {c['text']}")
        out.append("-"*112)
    tp.write_text("\n".join(out)+"\n",encoding="utf-8")
    print("="*112)
    print("TFT INSIGHT / ROADMAP 25.0P - RUNTIME CONFIG & WEBSOCKET EVIDENCE MAPPER")
    print("="*112)
    print("Arquivos lidos :",scanned)
    print("Com pistas     :",len(results))
    print("TXT            :",tp)
    print("Envie o TXT.")
if __name__=="__main__": main()
