"""Probe Krisinformation v3 historical coverage without changing dashboard data."""
from __future__ import annotations
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://api.krisinformation.se/v3/news"
WINDOWS = (7, 30, 365, 3650)
FIELDS = ["article_id","title","published_at","updated_at","url","area_json","summary","retrieved_at"]
def request(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent":"Lulea-statistik/krisinformation-historical-audit","Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=65) as res:
        return json.load(res)
def records(payload):
    if isinstance(payload,list): return payload
    if isinstance(payload,dict):
        for key in ("news","News","items","Items","data","Data","results","Results"):
            inner=payload.get(key)
            if isinstance(inner,list): return inner
            if isinstance(inner,dict):
                nested=records(inner)
                if nested is not None: return nested
    return None
def value(r,*names):
    for n in names:
        v=r.get(n)
        if v is not None: return v
    return ""
def flat(v):
    if isinstance(v,(dict,list)): return json.dumps(v,ensure_ascii=False)
    return str(v or "")
def main():
    DATA.mkdir(exist_ok=True)
    stats=[]
    selected={}
    for days in WINDOWS:
        params={"language":"sv","counties":"25","days":days}
        try:
            payload=request(params)
            items=records(payload)
            if items is None: raise ValueError("Unsupported top level "+str(type(payload)))
            valid=[r for r in items if isinstance(r,dict)]
            stats.append({"days":days,"status":"ok","returned":len(valid),
                "fields":",".join(sorted({k for r in valid[:4] for k in r.keys()})),
                "error":""})
            for r in valid:
                ident=flat(value(r,"Id","id","ID","identifier","Identifier"))
                if ident: selected[ident]=r
        except Exception as exc:
            stats.append({"days":days,"status":"error","returned":0,"fields":"",
                "error":str(exc)[:350]})
    with (DATA/"krisinformation_api_probe.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["days","status","returned","fields","error"])
        w.writeheader();w.writerows(stats)
    now=datetime.now(timezone.utc).isoformat()
    with (DATA/"krisinformation_norrbotten_candidate.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        for ident,r in sorted(selected.items()):
            w.writerow({"article_id":ident,
                "title":flat(value(r,"Headline","headline","Title","title")),
                "published_at":flat(value(r,"Published","published","PublishedAt","publishedAt","Date","date")),
                "updated_at":flat(value(r,"Updated","updated","UpdatedAt","updatedAt","Modified","modified")),
                "url":flat(value(r,"Link","link","Url","url","WebUrl","webUrl")),
                "area_json":flat(value(r,"Area","area","Areas","areas")),
                "summary":flat(value(r,"Preamble","preamble","Summary","summary","Text","text"))[:1000],
                "retrieved_at":now})
    print("window audit:", stats)
    print("deduplicated IDs:",len(selected))
    if not any(s["status"]=="ok" for s in stats):
        raise RuntimeError("All API probes failed; results saved but not validated")
if __name__=="__main__":main()
