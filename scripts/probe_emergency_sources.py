"""Bounded availability audit: Krisinformation VMA and SOS Inblick public page.

No historical or live incident metrics are published by this script.
"""
from __future__ import annotations
import csv
import json
import re
import urllib.request
from datetime import datetime,timezone
from html import unescape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"emergency_sources_probe.csv"
SOURCES={
 "vma_all":"https://api.krisinformation.se/v3/vmas?language=sv&allCounties=true",
 "vma_norrbotten":"https://api.krisinformation.se/v3/vmas?language=sv&counties=25",
 "sos_inblick_lulea":"https://www.sosalarm.se/inblick/kommuner/lulea-kommun/",
}
def fetch(url):
    request=urllib.request.Request(url,headers={"User-Agent":"Lulea-statistik-source-availability-audit/1.0","Accept":"application/json,text/html"})
    with urllib.request.urlopen(request,timeout=35) as response:
        return response.status,response.headers.get("Content-Type",""),response.read(2_000_000).decode("utf-8","replace")
def main():
    rows=[]
    for name,url in SOURCES.items():
        try:
            status,ctype,raw=fetch(url)
            if name.startswith("vma"):
                data=json.loads(raw)
                items=data if isinstance(data,list) else next((data.get(k) for k in ["items","data","vmas","results"] if isinstance(data.get(k),list)),None) if isinstance(data,dict) else None
                if items is None: raise ValueError("Unrecognized JSON structure")
                rows.append({"source":name,"http_status":status,"kind":"json","item_count":len(items),"fields":",".join(sorted(items[0].keys())) if items and isinstance(items[0],dict) else "","sample":"", "error":""})
            else:
                text=unescape(re.sub(r"<[^>]+>"," ",re.sub(r"<(script|style)[^>]*>.*?</\\1>"," ",raw,flags=re.I|re.S)))
                text=re.sub(r"\\s+"," ",text)
                # Availability only: dynamic content can differ from the rendered page.
                has_types=all(w.casefold() in text.casefold() for w in ["Polisen","Vårdbehov","Räddning"])
                rows.append({"source":name,"http_status":status,"kind":"html","item_count":"","fields":"categories_present="+str(has_types),"sample":text[:180],"error":""})
        except Exception as exc:
            rows.append({"source":name,"http_status":"","kind":"","item_count":"","fields":"","sample":"","error":str(exc)[:300]})
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["source","http_status","kind","item_count","fields","sample","error"])
        writer.writeheader();writer.writerows(rows)
    print(json.dumps(rows,ensure_ascii=False))
if __name__=="__main__":main()
