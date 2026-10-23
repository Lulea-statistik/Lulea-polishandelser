#!/usr/bin/env python3
"""Geometric DeSO overlap audit of named road centre-lines; never changes police statistics.

Inputs (geometries required; an Excel name list alone cannot establish extent):
 --roads: GeoPackage/GeoJSON with lines and a road-name attribute
 --deso:  SCB DeSO 2025 GeoPackage/GeoJSON with polygons and code attribute

The result measures *DeSO crossing*, NOT automatically inter-district roads.
A subsequent DeSO -> local district crosswalk is needed for publication decisions.
"""
import argparse,csv,sys,unicodedata,re
from collections import defaultdict
from pathlib import Path
import geopandas as gpd

def norm(value):
 return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",str(value or "")).casefold()).strip()

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--roads",required=True)
 p.add_argument("--deso",required=True)
 p.add_argument("--road-column",default="gatunamn")
 p.add_argument("--deso-column",default="DeSO")
 p.add_argument("--output",default="data/audit_lulea_road_deso_crossings.csv")
 p.add_argument("--min-meters",type=float,default=50)
 p.add_argument("--min-share",type=float,default=0.02)
 a=p.parse_args()
 roads=gpd.read_file(a.roads);deso=gpd.read_file(a.deso)
 for df,key in [(roads,a.road_column),(deso,a.deso_column)]:
  if key not in df.columns:raise ValueError(f"Missing {key}; available: {df.columns.tolist()}")
  if df.crs is None:raise ValueError("Input geometries must define CRS")
 roads=roads[roads.geometry.notna() & ~roads.geometry.is_empty].copy()
 deso=deso[deso.geometry.notna() & ~deso.geometry.is_empty].copy()
 roads["road_name"]=roads[a.road_column].map(norm)
 roads=roads[roads.road_name.ne("")].copy()
 deso["deso_id"]=deso[a.deso_column].astype(str)
 # SWEREF99 TM supports metric intersection/length comparison for northern Sweden.
 roads=roads.to_crs(3006);deso=deso.to_crs(3006)
 roads=roads[roads.geom_type.isin(["LineString","MultiLineString"])]
 deso=deso[deso.geom_type.isin(["Polygon","MultiPolygon"])]
 # Avoid counting adjacent polygons at shared boundaries twice:
 # only measurable intersected line length contributes.
 road_segments=roads[["road_name","geometry"]].dissolve(by="road_name",as_index=False)
 pairs=gpd.overlay(road_segments,deso[["deso_id","geometry"]],how="intersection",keep_geom_type=True)
 pairs["length_m"]=pairs.geometry.length
 road_lengths=dict(zip(road_segments.road_name,road_segments.geometry.length))
 dist=defaultdict(dict)
 for record in pairs.itertuples(index=False):
  name=record.road_name;code=record.deso_id
  dist[name][code]=dist[name].get(code,0)+record.length_m
 result=[]
 for name in sorted(road_lengths):
  total=road_lengths[name];lengths=dist.get(name,{})
  qualifying={k:v for k,v in lengths.items() if v>=a.min_meters and (total<=0 or v/total>=a.min_share)}
  status=("Passerar flera DeSO" if len(qualifying)>1 else
          "Inom ett DeSO" if len(qualifying)==1 else
          "Otillräcklig DeSO-täckning")
  result.append({"road_name":name,"road_total_m":round(total,1),
   "deso_count_raw":len(lengths),"deso_count_significant":len(qualifying),
   "deso_codes":" | ".join(sorted(qualifying)),"classification_deso":status,
   "classification_district":"Ej avgjord – kräver stadsdelsgeometri/koppling"})
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=result[0].keys());w.writeheader();w.writerows(result)
 print("ROAD_DESO_QA",{"named_roads":len(result),"multiple_deso":sum(x["classification_deso"]=="Passerar flera DeSO" for x in result),"single_deso":sum(x["classification_deso"]=="Inom ett DeSO" for x in result),"unresolved":sum(x["classification_deso"]=="Otillräcklig DeSO-täckning" for x in result)})
 print("GIS PREVIEW ONLY; no published police geography changed")
if __name__=="__main__":main()
