#!/usr/bin/env python3
"""QA-only: ArcGIS municipality district polygon source and OSM road-length overlay."""
import csv,json,urllib.request,urllib.parse,os
from pathlib import Path
import geopandas as gpd
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
SERVICE=os.environ.get("LULEA_DISTRICT_FEATURE_LAYER","").strip()
if not SERVICE:
 raise SystemExit("Stadsdelslager för Luleå saknas. Det tidigare lagret tillhör Gävle. Ange ett kontrollerat LULEA_DISTRICT_FEATURE_LAYER från Luleå kommuns geodataportal.")
G=ROOT/"data/gis"
def get(params,path=""):
 req=urllib.request.Request(SERVICE+path+"?"+urllib.parse.urlencode(params),headers={"User-Agent":"lulea-statistik-district-geography-qa/1.0"})
 with urllib.request.urlopen(req,timeout=80) as response:return json.load(response)
def main():
 meta=get({"f":"json"})
 if meta.get("error"):raise RuntimeError(meta["error"])
 if meta.get("geometryType")!="esriGeometryPolygon":raise ValueError("Not polygon geometry")
 fields=[x["name"] for x in meta.get("fields",[])]
 print("STADSDEL_LAYER_METADATA",json.dumps({"name":meta.get("name"),"fields":fields,"extent":meta.get("extent"),"description":meta.get("description")},ensure_ascii=False),flush=True)
 candidates=["namn","Namn","NAMN","Name","name","Stadsdel","stadsdel","STADSDEL","omr_namn","OMR_NAMN","Summeringsomrade","summeringsomrade","omradesnamn","Omradesnamn"]
 namefield=next((x for x in candidates if x in fields),None)
 if not namefield:raise ValueError("No verified district name field; inspect metadata instead of inferring")
 ids=get({"f":"json","returnIdsOnly":"true","where":"1=1"},"/query")
 if "error" in ids:raise RuntimeError("ArcGIS object ID query failed: "+json.dumps(ids["error"],ensure_ascii=False))
 objectids=ids.get("objectIds") or []
 if not objectids:raise ValueError("No polygon object IDs")
 features=[]
 for pos in range(0,len(objectids),100):
  q=get({"f":"geojson","objectIds":",".join(map(str,objectids[pos:pos+100])),"outFields":"*","outSR":"4326"},"/query")
  if q.get("type")!="FeatureCollection":raise ValueError("ArcGIS query did not return GeoJSON: "+str(q)[:400])
  features.extend(q.get("features",[]))
 if len(features)!=len(objectids):raise ValueError(("Incomplete features",len(features),len(objectids)))
 district=gpd.GeoDataFrame.from_features(features,crs=4326)
 district=district[district.geometry.notna()&~district.geometry.is_empty].to_crs(3006)
 district["district"]=district[namefield].astype(str).str.strip()
 if district.district.eq("").any():raise ValueError("Unlabelled districts")
 deso=gpd.read_file(G/"scb_deso_2025_lulea.geojson").to_crs(3006)
 municipal=unary_union(deso.geometry)
 overlap=district.geometry.intersection(municipal).area.sum()
 district_area=district.geometry.area.sum()
 coverage=overlap/district_area if district_area else 0
 print("STADSDEL_LAYER_QA",json.dumps({"polygon_count":len(district),"names":sorted(district.district.unique().tolist()),"area_overlap_lulea_fraction":round(coverage,3)},ensure_ascii=False),flush=True)
 if coverage<0.97:raise ValueError("Polygon layer is not predominantly in Lulea municipality")
 roads=gpd.read_file(G/"osm_eight_roads_lulea_clipped.geojson").to_crs(3006)
 if len(roads)!=239:raise ValueError(("Unexpected pilot roads",len(roads)))
 out=[]
 for name, subset in district.groupby("district"):
  polygon=unary_union(subset.geometry)
  for road, segs in roads.groupby("road_name"):
   geom=unary_union(segs.geometry)
   length=geom.intersection(polygon).length
   if length>0:out.append({"geography_type":"Stadsdel – GIS-pilot","geography_code":name,"geography_label":name,"road":road,"road_total_m":round(geom.length,1),"length_in_geography_m":round(length,1),"data_quality":"GIS pilot – municipal polygon and OSM 8 roads"})
 payload={"metadata":{"scope":"Endast 8 pilotvägar – inte ett komplett gatunät","geography":"Stadsdelspolygoner, geometri-verifierad mot Luleå kommun","source":SERVICE,"min_m_exclusive":1000,"max_m_inclusive":5000},"rows":out}
 dest=ROOT/"docs/data/road_lengths_stadsdel_pilot.json"
 dest.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
 print("STADSDEL_ROAD_RESULTS",json.dumps({"roads":len(set(x["road"] for x in out)),"districts":len(set(x["geography_code"] for x in out)),"rows":len(out),"filtered_rows":sum(1000<x["length_in_geography_m"]<=5000 for x in out)},ensure_ascii=False))
 print("QA only; no police incident geography modified")
if __name__=="__main__":main()
