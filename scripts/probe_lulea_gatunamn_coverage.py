#!/usr/bin/env python3
"""Audit ArcGIS Gatunamn service counts, metadata, extent and sample geography; no download."""
import json,urllib.request,urllib.parse
BASE="https://services-eu1.arcgis.com/yMpV9pwoiLaEREin/ArcGIS/rest/services/Gatunamn/FeatureServer/0"
def query(path,params):
 url=BASE+path+"?"+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={"User-Agent":"Lulea-statistik-geodata-qa/1.0"})
 with urllib.request.urlopen(req,timeout=70) as resp:data=json.load(resp)
 if "error" in data:raise RuntimeError(data["error"])
 return data
m=query("",{"f":"json"})
print("ROAD_LAYER_METADATA",json.dumps({k:m.get(k) for k in ("name","geometryType","extent","copyrightText","description","serviceItemId","maxRecordCount","advancedQueryCapabilities")},ensure_ascii=False))
c=query("/query",{"f":"json","where":"1=1","returnCountOnly":"true"})
print("ROAD_LAYER_COUNT",c)
samples=query("/query",{"f":"geojson","where":"1=1","outFields":"NVDB_DK_130,RoadwayID","returnGeometry":"true","resultRecordCount":"10","orderByFields":"OBJECTID ASC"})
features=samples.get("features",[])
print("ROAD_LAYER_FIRST_SAMPLE",json.dumps([{"name":x.get("properties",{}).get("NVDB_DK_130"),"roadway_id":x.get("properties",{}).get("RoadwayID"),"coordinates_head":str(x.get("geometry",{}).get("coordinates",[]))[:90]} for x in features],ensure_ascii=False))
print("Metadata/sample only; geographic coverage and ownership still subject to verification.")
