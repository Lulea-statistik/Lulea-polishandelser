#!/usr/bin/env python3
"""Verifierade kommunpar som ryms helt i ett lokalpolisområde.

Händelser med otydliga kombinationer eller över LPO-gränser tas inte med.
Ursprunglig serie: varje originalpost; expanderad: endast självständig
icke-sammanfattning eller ej uppdelad sammanfattning. Inga underhändelser
ärver automatiskt förälderns kommunpar.
"""
import csv
from pathlib import Path
from collections import defaultdict
from build_expanded_monthly import admin_non_event, NO_NEW_EVENT_RE

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/events.csv"
DETAILS=ROOT/"data/summary_details_dedup.csv"
OUT=ROOT/"docs/data/local_police_area_pairs_monthly.csv"
AREAS={
"Lokalpolisområde Luleå/Boden":{"Boden","Luleå"},
"Lokalpolisområde Piteå Älvdal":{"Piteå","Älvsbyn","Arvidsjaur","Arjeplog"},
"Lokalpolisområde Norra Lappland":{"Kiruna","Gällivare","Jokkmokk"},
"Lokalpolisområde Östra Norrbotten":{"Haparanda","Kalix","Pajala","Överkalix","Övertorneå"}}
def truth(v):return str(v or "").lower() in ("true","1")
def month(r):
 try:
  v=int(r.get("month",0))
  return f"{v:02d}" if 1<=v<=12 else None
 except (ValueError,TypeError):return None
with DETAILS.open(encoding="utf-8-sig",newline="") as f:
 parsed={r.get("parent_event_id","") for r in csv.DictReader(f)}
counts=defaultdict(int); seen=set()
with SRC.open(encoding="utf-8-sig",newline="") as f:
 for r in csv.DictReader(f):
  if r.get("geography_group")!="Flera kommuner i Norrbotten":continue
  source=r.get("municipality_source","")
  if not source.startswith("municipality_pair:"):continue
  pair=set(x.strip() for x in source.split(":",1)[1].split("|") if x.strip())
  if len(pair)!=2:continue
  matched=[area for area,members in AREAS.items() if pair<=members]
  if len(matched)!=1:continue
  eid=r.get("event_id","")
  if eid and eid in seen:continue
  if eid:seen.add(eid)
  mo=month(r);year=r.get("year","")
  if not mo or not year.isdigit():continue
  area=matched[0];typ=r.get("type_original") or "Okänd"
  counts[("original",year,mo,area,typ)]+=1
  if truth(r.get("is_summary")):
   if eid in parsed:continue
   text=" ".join(r.get(k,"") or "" for k in ("headline","description","content"))
   if NO_NEW_EVENT_RE.search(text):continue
   typ="Sammanfattning, ej uppdelad"
  elif admin_non_event(r):continue
  counts[("expanded",year,mo,area,typ)]+=1
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["series","year","month","geography_group","type_original","event_count"])
 for key,n in sorted(counts.items()):w.writerow([*key,n])
print("Verified same-LPO municipality-pair publications:",sum(n for k,n in counts.items() if k[0]=="original"))
