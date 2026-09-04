from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/discover_tft_process_ports_safe.py"
text = PROBE.read_text(encoding="utf-8") if PROBE.exists() else ""

checks = [
    ("Script presente", PROBE.exists()),
    ("Sintaxe valida", True),
    ("Processo alvo correto", 'TARGET_IMAGE = "League of Legends.exe"' in text),
    ("Usa tasklist", '"tasklist"' in text),
    ("Usa netstat", '"netstat"' in text),
    ("Nao usa requests", "requests" not in text),
    ("Nao abre socket", "socket." not in text),
    ("Sem port scan", '"port_scan": False' in text),
    ("Sem HTTP probe", '"http_probe": False' in text),
    ("Sem memoria", '"memory_reading": False' in text),
    ("Sem injecao", '"process_injection": False' in text),
    ("Sem sniffing", '"packet_sniffing": False' in text),
    ("Sem input", '"input_automation": False' in text),
]

for forbidden in (
    "OpenProcess",
    "ReadProcessMemory",
    "WriteProcessMemory",
    "VirtualAllocEx",
    "CreateRemoteThread",
    "scapy",
    "pydivert",
    "requests.get(",
    "requests.post(",
):
    checks.append(
        (f"Ausente: {forbidden}", forbidden.lower() not in text.lower())
    )

try:
    if PROBE.exists():
        ast.parse(text, filename=str(PROBE))
except SyntaxError:
    checks[1] = ("Sintaxe valida", False)

print("=" * 110)
print("#66 / ROADMAP 25.0J - PROCESS-BOUND PORT DISCOVERY GUARDRAILS")
print("=" * 110)

passed = 0
for i, (label, ok) in enumerate(checks, 1):
    passed += int(ok)
    print(f"[{i:02d}] {label:<84} {'OK' if ok else 'ERRO'}")

print("-" * 110)
print(f"PASSARAM: {passed}/{len(checks)}")

if passed != len(checks):
    raise SystemExit(1)

print("#66 ROADMAP 25.0J: PROCESS-BOUND PORT DISCOVERY VALIDADO")
