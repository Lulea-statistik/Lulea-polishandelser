#!/usr/bin/env python3
"""QA-only: combine archived OSM way artifacts and intersect with Lulea DeSO 2025.

Input ZIP artifacts are downloaded by the companion workflow, NOT scraped from a
live Overpass server. This is not a verified district/street classification.
"""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"data/gis/osm_archived"
OUTPUT=ROOT/"data/gis"
SOURCES=[
 ("Hertsövägen",1,39939493805),("Älvbrovägen",2,39940928508),
 ("Haparandavägen",3,39938662295),("Storhedsvägen",4,39938662295),
 ("Mariebergsvägen",5,39939493805),("Mjölkuddsvägen",6,39939493805),
 ("Storsandsvägen",7,39939493805),("Väderleden",8,39939493805),
]
def main():
 deso_path=OUTPUT/"scb_deso_2025_lulea.geojson"
 deso=gpd.read_file(deso_path)
 assert len(deso)==48,("Unexpected SCB DeSO count",len(deso))
 assert "desokod" in deso.columns
 assert "kommunkod" in deso.columns
 assert set(deso.kommunkod.astype(str))=={"2580"}
 deso=deso.to_crs(3006)
 # Dissolve polygons to municipality; avoid out-of-commune bounding-box false hits.
 municipality=unary_union(deso.geometry)
 lines=[];manifest=[];seen=set()
 for road,number,run in SOURCES:
  p=INPUT/f"road_{number}"/f"osm_lulea_{number}_road_candidates.geojson"
  obj=json.loads(p.read_text(encoding="utf-8"))
  ways=0
  for f in obj["features"]:
   props=f.get("properties") or {}
   name=props.get("road_name","")
   assert name.casefold()==road.casefold(),(road,name)
   osm_id=props.get("osm_way_id")
   k=(road.casefold(),osm_id)
   if k in seen:continue
   seen.add(k)
   g=shape(f["geometry"])
   assert g.geom_type in ("LineString","MultiLineString") and not g.is_empty
   lines.append({"road_name":road,"osm_way_id":osm_id,"source_run":run,"geometry":g})
   ways+=1
  assert ways>0,("Missing OSM ways",road)
  manifest.append({"road_name":road,"source_run":run,"ways":ways})
 raw=gpd.GeoDataFrame(lines,geometry="geometry",crs="EPSG:4326").to_crs(3006)
 clipped=raw.copy()
 clipped["geometry"]=clipped.geometry.intersection(municipality)
 clipped=clipped[~clipped.geometry.is_empty].copy()
 clipped=clipped[clipped.geometry.length>0].copy()
 clipped.to_crs(4326).to_file(OUTPUT/"osm_eight_roads_lulea_clipped.geojson",driver="GeoJSON")
 rows=[]
 for road,_,run in SOURCES:
  original=raw[raw.road_name==road]
  inside=clipped[clipped.road_name==road]
  # Union each named road to avoid counting overlapping ways in total.
  orig_u=unary_union(original.geometry); in_u=unary_union(inside.geometry)
  orig_m=orig_u.length; inside_m=in_u.length
  overlaps={}
  for record in deso.itertuples(index=False):
   length=in_u.intersection(record.geometry).length
   if length>0:overlaps[str(record.desokod)]=length
  significant={k:v for k,v in overlaps.items() if v>=50 and (inside_m>0 and v/inside_m>=.02)}
  fraction=inside_m/orig_m if orig_m else 0
  coverage=sum(overlaps.values())/inside_m if inside_m else 0
  status=("kräver granskning – låg kommun/DeSO-täckning" if fraction<.95 or coverage<.95
          else "flera DeSO – stadsdelsklass okänd" if len(significant)>1
          else "ett DeSO – stadsdelsklass okänd" if len(significant)==1
          else "kräver granskning – gränseffekt")
  rows.append({"road_name":road,"source_run":run,"osm_ways":len(original),
   "total_m":round(orig_m,1),"inside_lulea_m":round(inside_m,1),
   "fraction_in_lulea":round(fraction,4),"deso_coverage_fraction":round(coverage,4),
   "deso_significant_count":len(significant),"deso_significant_codes":" | ".join(sorted(significant)),
   "deso_lengths_m":json.dumps({k:round(v,1) for k,v in sorted(overlaps.items())},ensure_ascii=False),
   "deso_audit":status,"district_classification":"Ej bedömd","publication":"Nej"})
 with (OUTPUT/"audit_osm_eight_roads_deso_2025.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 (OUTPUT/"audit_osm_eight_roads_sources.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
 print("ROAD_DESO_PILOT",json.dumps({"road_count":len(rows),"original_osm_ways":len(raw),"clipped_segments":len(clipped),"status_counts":dict(Counter(x["deso_audit"] for x in rows))},ensure_ascii=False))
 for item in rows:print("ROAD_DESO_RESULT",json.dumps(item,ensure_ascii=False))
 print("NO PUBLICATION: DeSO intersection is not district classification")
if __name__=="__main__":main()
