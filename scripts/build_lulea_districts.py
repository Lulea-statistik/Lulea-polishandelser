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
 "Bergviken": ["bergviken", "midgardsvagen", "midgårdsvägen", "delfinvagen", "delfinvägen", "hummergatan"],
 "Björkskatan": ["bjorkskatan", "björkskatan", "vaderleden", "väderleden"],
 "Centrum": [
  "centrum", "lulea centrum", "luleå centrum", "innerstaden", "lulea innerstad", "luleå innerstad",
  "stadsviken", "charlottendal", "norra hamn", "norra hamnen", "sodra hamn", "södra hamn", "sodra hamnen", "södra hamnen", "ostermalm", "östermalm",
  "gultzauudden", "gültzauudden", "gultzaudden", "gültsauudden", "vastra stranden", "västra stranden", "oscarsvarv",
  "storgatan", "smedjegatan", "radstugatan", "rådstugatan", "radstugugatan", "rådstugugatan",
  "jarnvagsstation", "järnvägsstation", "jarnvagsstationen", "järnvägsstationen", "lulea centralstation", "luleå centralstation",
  "kopmantorget", "köpmantorget", "kungsgatan", "stationsgatan", "skeppsbrogatan", "sandviksgatan",
  "busstationen", "busstation", "lulea busstation", "luleå busstation", "sodra hamnleden", "södra hamnleden",
  "lulea c", "luleå c", "kulturens hus", "stadsparken", "gymnasiebyn", "gymnasieby",
  "lulea domkyrka", "luleå domkyrka", "domkyrkan", "lulea energi arena", "luleå energi arena", "pontushallen",
  "smedjan galleria", "smedjan", "strand galleria", "shopping galleria", "shoppinghuset",
  "hermelinsparken", "jarnvagsparken", "järnvägsparken", "residensparken",
  "pontusbadet", "halsans hus", "hälsans hus", "norrbottensteatern", "norrbottens museum",
  "skomakargatan", "bastugatan", "residensgatan", "norra hamnpromenaden",
  "sodra hamnplan", "södra hamnplan",
  "hermelinsgatan", "sodra smedjegatan", "södra smedjegatan", "smabatsgatan", "småbåtsgatan",
  "prastgatan", "prästgatan", "tullgatan", "kopmangatan", "köpmangatan", "magasinsgatan",
  "norra strandgatan", "vastra varvsgatan", "västra varvsgatan", "centrumhallplatsen", "centrumhållplatsen",
  "sodra hamnkranen", "södra hamnkranen", "hamnkranen", "karpen parkeringshus", "parkeringshuset karpen",
  "sodra hamnterminalen", "södra hamnterminalen", "lulea stadshus", "luleå stadshus", "lulea stadsbibliotek", "luleå stadsbibliotek",
 ],
 "Gammelstad": ["gammelstad"],
 "Hertsön": ["hertson", "hertsön"],
 "Hertsöheden": ["hertsoheden", "hertsöheden"],
 "Kallkällan": ["kallkallan", "kallkällan"],
 "Karlsvik": ["karlsvik"],
 "Kronan": ["kronan"],
 "Lerbäcken": ["lerbacken", "lerbäcken"],
 "Malmudden": ["malmudden", "lulea malmudden", "luleå malmudden"],
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
MULTI = "Flera stadsdelar i Luleå"
MULTI_ROADS = ["svartovagen", "hertsovagen", "bergnasbron", "bergnäsbron"]
def normalize(s):
 s = unicodedata.normalize("NFKD",str(s or "").casefold())
 s = "".join(c for c in s if not unicodedata.combining(c))
 return re.sub(r"\s+"," ",s)
ROAD_PATTERNS = [re.compile(r"(?<![a-z])"+re.escape(normalize(road))+r"(?![a-z])") for road in MULTI_ROADS]
PATTERNS = {name:[re.compile(r"(?<![a-z])"+re.escape(normalize(alias))+r"(?![a-z])") for alias in al] for name,al in ALIASES.items()}
# Den snäva listan är uttryckligen godkänd för Centrum; ett naket omnämnande
# i löptexten räcker inte. "till/från busstationen" ska inte räknas.
NARRATIVE_CENTRUM = re.compile(
 r"(?<![a-z])(?:i|pa|vid|intill|utanfor|inne i|omkring|kring)\s+"
 r"(?:lulea\s+)?(?:innerstaden|centrum|busstationen|busstation)(?![a-z])"
)
# Snäva områdesnamn med tydlig platsinledning. Gatunamn från aliases
# läggs inte automatiskt till här: de kräver särskild adressgranskning.
NARRATIVE_DISTRICT_NAMES={
 "Bergnäset":["bergnaset"],"Bergviken":["bergviken"],
 "Björkskatan":["bjorkskatan"],"Gammelstad":["gammelstad"],
 "Hertsön":["hertson"],"Hertsöheden":["hertsoheden"],
 "Kallkällan":["kallkallan"],"Karlsvik":["karlsvik"],
 "Kronan":["kronan"],"Lerbäcken":["lerbacken"],
 "Malmudden":["malmudden"],"Mjölkudden":["mjolkudden"],
 "Munksund":["munksund"],"Notviken":["notviken"],
 "Porsön":["porson"],"Råneå":["ranea"],
 "Skurholmen":["skurholmen"],"Storheden":["storheden"],
 "Sunderbyn":["sunderbyn"],"Svartöstaden":["svartostaden"],
 "Örnäset":["ornaset"]}
NARRATIVE_DISTRICT_PATTERNS={
 district:re.compile(r"(?<![a-z])(?:i|pa|vid|intill|utanfor|kring)\s+(?:lulea\s+)?(?:"+"|".join(names)+r")(?![a-z])")
 for district,names in NARRATIVE_DISTRICT_NAMES.items()
}
def district(row):
 text=normalize(" ".join((row.get("title_location") or "",row.get("location_string") or "")))
 matches={name for name,pats in PATTERNS.items() if any(p.search(text) for p in pats)}
 if len(matches)>1: return MULTI
 if len(matches)==1: return next(iter(matches))
 if any(p.search(text) for p in ROAD_PATTERNS): return MULTI
 # Använd löptext bara om platsfält inte redan ger säker stadsdel.
 narrative=normalize(" ".join((row.get(k) or "") for k in ("headline","description","content")))
 candidates={name for name,pattern in NARRATIVE_DISTRICT_PATTERNS.items() if pattern.search(narrative)}
 if NARRATIVE_CENTRUM.search(narrative):candidates.add("Centrum")
 if len(candidates)==1:
  selected=next(iter(candidates))
  # Blockera när en annan stadsdel, bro eller lång väg också omnämns.
  others={name for name,pats in PATTERNS.items() if name!=selected and any(p.search(narrative) for p in pats)}
  if not others and not any(p.search(narrative) for p in ROAD_PATTERNS):
   return selected
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
