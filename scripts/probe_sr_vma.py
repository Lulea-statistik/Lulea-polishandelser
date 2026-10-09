"""Bounded diagnostic of Sveriges Radio's official VMA v3 API.

Tests only the live production endpoint and records schema/availability.
Does not manufacture historical data or include test/exercise alerts in statistics.
"""
from __future__ import annotations
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"sr_vma_api_probe.csv"
URL="https://vmaapi.sr.se/api/v3/alerts"

def main():
    request=urllib.request.Request(URL,headers={
        "User-Agent":"Lulea-statistik-SR-VMA-availability-test/1.0",
        "Accept":"application/json"
    })
    record={"source":"Sveriges Radio VMA v3","endpoint":URL,
        "checked_at":datetime.now(timezone.utc).isoformat(),
        "http_status":"","item_count":"","json_type":"",
        "available_fields":"","status_values":"","message_types":"","sample_area":"","error":""}
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            record["http_status"]=response.status
            payload=json.load(response)
        record["json_type"]=type(payload).__name__
        if isinstance(payload,list):
            items=payload
        elif isinstance(payload,dict):
            items=next((payload[k] for k in ["alerts","Alerts","items","data"]
                 if isinstance(payload.get(k),list)),None)
        else:
            items=None
        if items is None:
            raise ValueError("Unexpected JSON envelope; top-level keys: "+str(list(payload)[:12]) if isinstance(payload,dict) else "Unexpected API content")
        record["item_count"]=len(items)
        if items:
            record["available_fields"]="|".join(sorted({k for row in items[:10] if isinstance(row,dict) for k in row.keys()}))
            record["status_values"]="|".join(sorted({str(row.get("status","")) for row in items if isinstance(row,dict)}))
            record["message_types"]="|".join(sorted({str(row.get("msgType","")) for row in items if isinstance(row,dict)}))
            record["sample_area"]=json.dumps(items[0].get("info",[]),ensure_ascii=False)[:320] if isinstance(items[0],dict) else ""
    except Exception as exc:
        record["error"]=str(exc)[:420]
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(record))
        writer.writeheader();writer.writerow(record)
    print(json.dumps(record,ensure_ascii=False))
    if record["error"]:
        raise RuntimeError(record["error"])

if __name__=="__main__":
    main()
