#!/usr/bin/env python3
"""OSM/Overpass candidate geometry pilot for 8 audited Lulea roads; QA only."""
import argparse,json,re,sys,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from fetch_scb_deso_2025_lulea import ENDPOINT
ROADS=["Hertsövägen","Älvbrovägen","Haparandavägen","Storhedsvägen","Mariebergsvägen","Mjölkuddsvägen","Storsandsvägen","Väderleden"]
ROAD_SET={x.casefold() for x in ROADS}
DESO=ROOT/"data/gis/scb_deso_2025_lulea.geojson"
OUT=ROOT/"data/gis/osm_lulea_eight_road_candidates.geojson"
def download_scb():
 params={"service":"WFS","version":"2.0.0","request":"GetFeature","typeNames":"stat:DeSO_2025","outputFormat":"application/json","srsName":"EPSG:4326","CQL_FILTER":"kommunkod='2580'","count":"1000"}
 req=urllib.request.Request(ENDPOINT+"?"+urllib.parse.urlencode(params),headers={"User-Agent":"lulea-statistik-road-geometry-pilot/1.0"})
 with urllib.request.urlopen(req,timeout=90) as res:return json.load(res)
def coords(g):
 if isinstance(g,dict):yield from coords(g.get("coordinates",[]))
 elif isinstance(g,list):
  if len(g)>=2 and all(isinstance(x,(int,float)) for x in g[:2]):yield g[:2]
  else:
   for item in g:yield from coords(item)
def fetch_osm(bbox,selected_roads):
 south,west,north,east=bbox
 # A single large eight-name regex query caused an HTTP 504. Query each name
 # independently with bounded retries across public Overpass mirrors.
 endpoints=["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
 collected=[];failures=[]
 for name in selected_roads:
  # Anchored literal names; limit to named highway ways, and keep request small.
  qname=re.escape(name).replace('"',r'\"')
  query=f'[out:json][timeout:45];way["highway"]["name"="{qname}"]({south},{west},{north},{east});out geom;'
  payload=urllib.parse.urlencode({"data":query}).encode()
  succeeded=False
  for endpoint in endpoints:
   try:
    req=urllib.request.Request(endpoint,data=payload,headers={"User-Agent":"lulea-statistik-geodata-pilot/1.0"})
    with urllib.request.urlopen(req,timeout=65) as res:
     data=json.load(res)
    if "remark" in data and not data.get("elements"):raise RuntimeError(data["remark"])
    collected.extend(data.get("elements",[]))
    print("ROAD_OVERPASS_FETCH",json.dumps({"road":name,"endpoint":endpoint,"ways":len(data.get("elements",[]))},ensure_ascii=False))
    succeeded=True
    break
   except (OSError,ValueError,RuntimeError) as e:
    print("ROAD_OVERPASS_RETRY",json.dumps({"road":name,"endpoint":endpoint,"error":str(e)[:160]},ensure_ascii=False),flush=True)
  if not succeeded:failures.append(name)
  time.sleep(1)
 if failures:raise RuntimeError("Incomplete Overpass download for roads: "+", ".join(failures))
 return {"elements":collected}
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--road",choices=ROADS,required=True)
 args=parser.parse_args()
 obj=download_scb()
 feats=obj.get("features",[])
 if len(feats)!=48 or any(str(f.get("properties",{}).get("kommunkod"))!="2580" for f in feats):raise ValueError("Unexpected Lulea DeSO features")
 xy=[p for f in feats for p in coords(f.get("geometry",{}))]
 west=min(x for x,y in xy);east=max(x for x,y in xy);south=min(y for x,y in xy);north=max(y for x,y in xy)
 if not (19<west<25 and 19<east<26 and 64<south<67 and 64<north<67):raise ValueError("DeSO bounding box is not in Lulea")
 print("ROAD_PILOT_BOUNDING_BOX",{"south":south,"west":west,"north":north,"east":east,"deso":len(feats)})
 osm=fetch_osm((south,west,north,east),[args.road])
 elements=osm.get("elements",[])
 result=[];found={}
 for w in elements:
  tags=w.get("tags") or {};name=tags.get("name","");geom=w.get("geometry") or []
  if w.get("type")!="way" or name.casefold() not in ROAD_SET or len(geom)<2:continue
  pts=[[p["lon"],p["lat"]] for p in geom if "lon" in p and "lat" in p]
  if len(pts)<2:continue
  found[name]=found.get(name,0)+1
  result.append({"type":"Feature","properties":{"road_name":name,"osm_way_id":w["id"],"source":"OpenStreetMap contributors / Overpass","qa_status":"candidate_not_verified"},"geometry":{"type":"LineString","coordinates":pts}})
 if not result:raise ValueError("No named road candidate ways for "+args.road+": check Overpass endpoint / response")
 dest=OUT.with_name("osm_lulea_"+str(ROADS.index(args.road)+1)+"_road_candidates.geojson")
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps({"type":"FeatureCollection","features":result},ensure_ascii=False),encoding="utf-8")
 print("ROAD_PILOT_RESULTS",{"ways":len(result),"distinct_roads":len(found),"by_road":dict(sorted(found.items())),"missing_names":sorted({args.road}-set(found))})
 print("PILOT ONLY: bbox candidates not yet clipped to municipality/DeSO; no changes to published statistics")
if __name__=="__main__":main()
