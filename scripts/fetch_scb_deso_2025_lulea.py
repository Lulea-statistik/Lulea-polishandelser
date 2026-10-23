#!/usr/bin/env python3
"""Download SCB DeSO 2025 boundaries for Lulea (kommunkod 2580). QA only."""
import argparse,json,urllib.parse,urllib.request
from pathlib import Path
ENDPOINT="https://geodata.scb.se/geoserver/stat/wfs"
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",default="data/gis/scb_deso_2025_lulea.geojson");a=p.parse_args()
 params={"service":"WFS","version":"2.0.0","request":"GetFeature","typeNames":"stat:DeSO_2025",
         "outputFormat":"application/json","srsName":"EPSG:4326","CQL_FILTER":"kommunkod='2580'","count":"1000"}
 url=ENDPOINT+"?"+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={"User-Agent":"lulea-statistik-gis-audit/1.0"})
 with urllib.request.urlopen(req,timeout=90) as resp:
  raw=resp.read()
 data=json.loads(raw)
 features=data.get("features",[])
 if data.get("type")!="FeatureCollection" or not features:raise ValueError("SCB did not return features: "+raw[:300].decode(errors="replace"))
 for feat in features:
  props=feat.get("properties") or {}
  if str(props.get("kommunkod"))!="2580":raise AssertionError(("Wrong municipality",props))
  if not props.get("desokod"):raise AssertionError(("Missing DeSO code",props))
  if not feat.get("geometry"):raise AssertionError(("Missing geometry",props))
 if len({str(f["properties"]["desokod"]) for f in features})!=len(features):raise AssertionError("Duplicate DeSO codes")
 dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 print("SCB_DESO_2025",{"municipality":"2580","polygons":len(features),"file":str(dest)})
 print("Data source:",url)
 print("No road crossings or published police classifications computed")
if __name__=="__main__":main()
