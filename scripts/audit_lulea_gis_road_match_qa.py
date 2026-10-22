#!/usr/bin/env python3
"""Non-publishing GIS dictionary cross-check of unknown road event locations."""
import csv,re,sys,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_lulea_unified_geography_preview import records
REFERENCE=ROOT/"data/lulea_gis_gatunamn_reference.csv"
def read(p):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def norm(v):
 return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",str(v or "")).casefold()).strip()
raw=read(REFERENCE)
assert len(raw)==1290,(len(raw),"Incomplete GIS reference")
named={norm(r["gatunamn"]) for r in raw if norm(r["is_named_road"])=="true"}
areas={norm(r["gatunamn"]) for r in raw if norm(r["is_named_road"])=="false"}
assert len(named)==1106 and len(areas)==184,(len(named),len(areas))
events={str(r.get("event_id") or "").strip():r for r in read(ROOT/"data/events.csv")}
details=read(ROOT/"data/summary_details_dedup.csv")
def own_place(record):
 eid=record["event_id"]
 if record["source"]=="underhändelse":
  try:return details[int(eid.rsplit("#",1)[1])].get("place_text") or ""
  except (IndexError,ValueError):return ""
 row=events.get(eid,{})
 return " ".join(row.get(k) or "" for k in ("title_location","location_string"))
def present(name,text):
 return bool(re.search(r"(?<!\w)"+re.escape(name)+r"(?!\w)",text))
# Restrict checks to candidates previously classified 'unknown road'.
rows=[];statuses=Counter()
for record in records:
 if record["classification"]!="väg-okänd":continue
 place=norm(own_place(record))
 # Avoid O(n*1,290) regex calls for missing or very short place fields.
 if not place:matches=[];localities=[]
 else:
  matches=[x for x in named if x in place and present(x,place)]
  localities=[x for x in areas if x in place and present(x,place)]
 if len(matches)==1 and not localities:status="En GIS-väg i eget platsfält – kontrollera händelserelation"
 elif len(matches)>1:status="Flera GIS-vägar – manuell granskning"
 elif localities:status="Områdesledtråd – ej namngiven väg"
 else:status="Ingen entydig GIS-träff"
 statuses[status]+=1
 rows.append({"event_id":record["event_id"],"source":record["source"],"original_geography":record["base_geography"],"place_text":own_place(record)[:300],"gis_road_candidates":" | ".join(sorted(matches)),"gis_area_clues":" | ".join(sorted(localities)),"review_status":status})
assert len(rows)==4265,(len(rows),"Unexpected number of unknown-road events")
out=ROOT/"data/audit_lulea_gis_road_match_qa.csv"
with out.open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print("GIS_DICTIONARY",{"named_roads":len(named),"area_clues":len(areas)})
print("GIS_UNKNOWN_ROAD_MATCH",dict(statuses),"total",len(rows))
print("PREVIEW ONLY; no public CSV updated")
