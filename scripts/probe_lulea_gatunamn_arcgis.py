#!/usr/bin/env python3
"""Probe suspected ArcGIS 'Gatunamn' service: metadata only, no police updates."""
import json,urllib.request,urllib.parse
BASE="https://services-eu1.arcgis.com/yMpV9pwoiLaEREin/ArcGIS/rest/services/Gatunamn/FeatureServer"
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Lulea-statistik-geodata-qa/1.0"})
 with urllib.request.urlopen(req,timeout=50) as res:return json.load(res)
root=get(BASE+"?f=pjson")
if "error" in root:raise RuntimeError(root["error"])
layers=root.get("layers",[])
print("GATUNAMN_SERVICE",{"layers":len(layers),"service":BASE})
if not layers:raise RuntimeError("No feature layers found")
for layer in layers:
 m=get(BASE+"/"+str(layer["id"])+"?f=pjson")
 fields=[{"name":f.get("name"),"alias":f.get("alias")} for f in m.get("fields",[])]
 print("GATUNAMN_LAYER",json.dumps({"id":layer["id"],"name":m.get("name"),"geometryType":m.get("geometryType"),"maxRecordCount":m.get("maxRecordCount"),"fields":fields},ensure_ascii=False))
print("Metadata inspected only. Before download verify provenance, municipality coverage, attributes, pagination and geometry.")
