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

# Priority report by name with distinct incident IDs and evidence examples.
from collections import defaultdict
by_name=defaultdict(list)
for x in rows:
 if x["review_status"].startswith("En GIS-väg"):
  by_name[x["gis_road_candidates"]].append(x)
priority=ROOT/"data/audit_lulea_gis_road_priority.csv"
with priority.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["gis_road_name","candidate_events","display_group_if_reviewed","example_event_ids","qa_status"])
 for name,group in sorted(by_name.items(),key=lambda kv:(-len(kv[1]),kv[0])):
  label=name if len(group)>=10 else "Övrig väg, känd väg"
  w.writerow([name,len(group),label," | ".join(str(x["event_id"]) for x in group[:8]),"Ej verifierad - granska händelserelation"])
assert sum(len(x) for x in by_name.values())==statuses["En GIS-väg i eget platsfält – kontrollera händelserelation"]
print("GIS_PRIORITY_TOP",[(name,len(group)) for name,group in sorted(by_name.items(),key=lambda kv:-len(kv[1]))[:25]])
print("GIS_PRIORITY_ROADS",len(by_name))
print("PREVIEW ONLY; no public CSV updated")
