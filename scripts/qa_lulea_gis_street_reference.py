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
assert len(roads)+len(areas)==len(rows)
# The source is *only* a vocabulary; never automatically assign a police event to a district or road.
