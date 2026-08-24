from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
load_dotenv(ROOT/".env")

from partner_platform.services.api_client import DashboardApiClient

game=input("Riot ID (Game Name): ").strip()
tag=input("Tag: ").strip()

client=DashboardApiClient(
    base_url=os.getenv("TFT_INSIGHT_API_BASE_URL","http://127.0.0.1:8000"),
    api_key=os.getenv("TFT_INSIGHT_API_KEY",""),
    timeout=180.0,
)

report=client.latest_post_match_report(
    game_name=game,
    tag_line=tag,
    skill_id="leveling",
    skill_label="Leveling",
    mission_title="Planejar o próximo nível",
    objective="Antes de gastar ouro, defina qual será seu próximo momento de subida de nível.",
    history_size=10,
)

print("\n"+"="*94)
print("ANÁLISE PÓS-PARTIDA V1.7")
print("="*94)
print(f"Partida  : {report.get('match_id','-')}")
print(f"Headline : {report.get('headline','-')}")
print("\nRESUMO\n"+"-"*94)
print(report.get("summary","-"))
print("\nFOCO\n"+"-"*94)
focus=report.get("focus_section",{}) or {}
print(focus.get("title","-"))
print(focus.get("text","-"))
print("\nPRÓXIMO JOGO\n"+"-"*94)
print(report.get("coach_takeaway","-"))
print("\nPROTEÇÕES\n"+"-"*94)
for key,value in (report.get("protections",{}) or {}).items():
    print(f"{key:<32}: {value}")
print("\n"+"="*94)
print("DIAGNÓSTICO CONCLUÍDO")
print("Depois valide visualmente na página Análise.")
print("="*94)
