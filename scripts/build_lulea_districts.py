#!/usr/bin/env python3
"""Försiktig delområdesklassning för enbart Luleå kommun.

Ingen geokodning eller implicit stadsdelsgissning: bara platsfälten används.
Osäkra / motstridiga platsuppgifter redovisas som Okänt delområde.
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/events.csv"
OUT = ROOT / "docs/data/lulea_district_monthly.csv"

ALIASES = {
 "Bergnäset": ["bergnaset", "bergnäset"],
 "Bergviken": ["bergviken"],
 "Björkskatan": ["bjorkskatan", "björkskatan"],
 "Centrum": [
  "centrum", "lulea centrum", "luleå centrum", "innerstaden", "lulea innerstad", "luleå innerstad",
  "stadsviken", "charlottendal", "norra hamn", "norra hamnen", "sodra hamn", "södra hamn", "sodra hamnen", "södra hamnen", "ostermalm", "östermalm",
  "gultzauudden", "gültzauudden", "gultzaudden", "gültsauudden", "vastra stranden", "västra stranden", "oscarsvarv",
  "storgatan", "smedjegatan", "radstugatan", "rådstugatan", "radstugugatan", "rådstugugatan",
  "jarnvagsstation", "järnvägsstation", "jarnvagsstationen", "järnvägsstationen", "lulea centralstation", "luleå centralstation",
  "kopmantorget", "köpmantorget", "kungsgatan", "stationsgatan", "skeppsbrogatan", "sandviksgatan",
  "busstationen", "busstation", "lulea busstation", "luleå busstation",
 ],
 "Gammelstad": ["gammelstad"],
 "Hertsön": ["hertson", "hertsön"],
 "Hertsöheden": ["hertsoheden", "hertsöheden"],
 "Kallkällan": ["kallkallan", "kallkällan"],
 "Karlsvik": ["karlsvik"],
 "Kronan": ["kronan"],
 "Lerbäcken": ["lerbacken", "lerbäcken"],
 "Mjölkudden": ["mjolkudden", "mjölkudden", "lulea mjolkudden", "luleå mjölkudden"],
 "Munksund": ["munksund"],
 "Notviken": ["notviken"],
 "Porsön": ["porson", "porsön"],
 "Råneå": ["ranea", "råneå"],
 "Skurholmen": ["skurholmen"],
 "Storheden": ["storheden"],
 "Sunderbyn": ["sunderbyn"],
 "Svartöstaden": ["svartostaden", "svartöstaden"],
 "Örnäset": ["ornaset", "örnäset"],
}
UNKNOWN = "Okänt delområde"
MULTI = "Flera områden i Luleå"
MULTI_ROADS = ["svartovagen", "hertsovagen"]
def normalize(s):
 s = unicodedata.normalize("NFKD",str(s or "").casefold())
 s = "".join(c for c in s if not unicodedata.combining(c))
 return re.sub(r"\s+"," ",s)
ROAD_PATTERNS = [re.compile(r"(?<![a-z])"+re.escape(normalize(road))+r"(?![a-z])") for road in MULTI_ROADS]
PATTERNS = {name:[re.compile(r"(?<![a-z])"+re.escape(normalize(alias))+r"(?![a-z])") for alias in al] for name,al in ALIASES.items()}
def district(row):
 # Do not use narrative / content: it may mention several places not at the event site.
 text=normalize(" ".join((row.get("title_location") or "",row.get("location_string") or "")))
 matches={name for name,pats in PATTERNS.items() if any(p.search(text) for p in pats)}
 if len(matches)>1: return MULTI
 if len(matches)==1: return next(iter(matches))
 if any(p.search(text) for p in ROAD_PATTERNS): return MULTI
 return UNKNOWN
def main():
 if not SOURCE.exists(): raise SystemExit("Missing events.csv")
 counts=defaultdict(int)
 ids=set()
 with SOURCE.open(encoding="utf-8-sig",newline="") as stream:
  reader=csv.DictReader(stream)
  required={"geography_group","title_location","location_string","type_original"}
  if not required.issubset(reader.fieldnames or []):raise SystemExit("Unexpected events.csv columns")
  for row in reader:
   if (row.get("geography_group") or "").strip()!="Luleå kommun":continue
   eid=(row.get("event_id") or "").strip()
   if eid:
    if eid in ids:continue
    ids.add(eid)
   year=(row.get("year") or "").strip()
   month=(row.get("month") or "").strip()
   if not year.isdigit() or not month.isdigit() or not (1<=int(month)<=12):continue
   month=f"{int(month):02d}"
   typ=(row.get("type_original") or "Okänd händelsetyp").strip()
   counts[(year,month,district(row),typ)]+=1
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open("w",encoding="utf-8",newline="") as stream:
  writer=csv.writer(stream);writer.writerow(["year","month","geography_group","type_original","event_count"])
  for key,n in sorted(counts.items()):writer.writerow([*key,n])
 print("Luleå-delområden:",sum(counts.values()),"unika händelser","kategorier:",len(counts))
if __name__=="__main__":main()
