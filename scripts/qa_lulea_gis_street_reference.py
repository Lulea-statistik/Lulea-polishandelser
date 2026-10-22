#!/usr/bin/env python3
"""Check Lulea GIS street-name inventory, without changing published event counts.

Optional: add data/reference/lulea_gis_gatunamn_reference.csv (UTF-8 CSV).
Flag true = named road, false = locality/area clue only.
"""
import csv,sys,unicodedata,re
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/reference/lulea_gis_gatunamn_reference.csv"
if not SOURCE.exists():
 print("GIS reference CSV missing. Upload lulea_gis_gatunamn_reference.csv to data/reference/ before running.");sys.exit(2)
with SOURCE.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
assert {"gatunamn","is_named_road","gis_segments"}<=set(rows[0]),"Missing expected headers"
def norm(v):
 v=unicodedata.normalize("NFKC",str(v or "")).casefold().strip()
 return re.sub(r"\\s+"," ",v)
roads={};areas={};duplicates=[]
for x in rows:
 name=norm(x["gatunamn"]);flag=norm(x["is_named_road"])
 assert flag in ("true","false"),("Unexpected GIS flag",x)
 target=roads if flag=="true" else areas
 if name in roads or name in areas:duplicates.append(name)
 target[name]=int(x["gis_segments"])
assert not duplicates,("Duplicate GIS reference names",duplicates[:10])
print("GIS_REFERENCE",{"named_roads":len(roads),"locality_clues":len(areas),"total_unique":len(rows)})
assert len(roads)==1106 and len(areas)==184 and len(rows)==1290, "Incomplete GIS register: require all 1290 unique names"
# The source is *only* a vocabulary; never automatically assign a police event to a district or road.

# Run a conservative dictionary review against the existing own-field road QA.
# Text-only matches do NOT trigger auto-geocoding.
from audit_lulea_own_place_road_qa import items
classified=Counter()
examples=defaultdict(list)
for item in items:
    place=norm(item["place_text"])
    found=[name for name in roads if re.search(r"(?<!\\w)"+re.escape(name)+r"(?!\\w)",place)]
    locality=[name for name in areas if re.search(r"(?<!\\w)"+re.escape(name)+r"(?!\\w)",place)]
    if len(found)==1 and not locality and item["review_status"].startswith("Entydig"):
        state="GIS-vägnamn, entydigt - verifiera platsrelation"; road=found[0]
    elif found or locality:
        state="Flertydig GIS-träff - manuell granskning";road=" | ".join(found[:5])
    else:
        state="Ingen säker GIS-namnträff";road=""
    classified[state]+=1
    examples[state].append((item["event_id"],road))
assert sum(classified.values())==len(items)
print("GIS_NAME_MATCH_QA",dict(classified))
output=ROOT/"data/audit_lulea_gis_street_match_qa.csv"
with output.open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f);w.writerow(["event_id","road_candidate","review_status"])
 for state,entries in examples.items():
  for eid,name in entries:w.writerow([eid,name,state])
print("QA output:",output)
