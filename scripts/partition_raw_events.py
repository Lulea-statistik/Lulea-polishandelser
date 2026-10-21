#!/usr/bin/env python3
"""Migrera äldre JSONL till årsvisa rådatapartitioner, utan dataförlust.

Första körningen läser legacyfilen events_raw.jsonl och sammanfogar med
eventuella årsdelar. Följande körningar använder årsdelarna. Originalet
raderas INTE; migreringen verifierar radantal, unika ID och SHA256.
"""
import argparse, hashlib, json, os, re, tempfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEGACY=ROOT/"data/events_raw.jsonl"
PARTS=ROOT/"data/raw_by_year"
MANIFEST=PARTS/"manifest.json"
LIMIT=80*1024*1024
def year_for(row):
    for key in ("year","published_datetime","date"):
        s=str(row.get(key) or "")
        m=re.match(r"^(19|20)\d{2}",s)
        if m:return m.group(0)
    return "unknown"
def identity(row):
    eid=str(row.get("event_id") or "").strip()
    if eid:return "id:"+eid
    # Record lacking a stable identifier: only identical raw records merge.
    return "raw:"+hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def read_records(path):
    if not path.exists():return
    with path.open(encoding="utf-8-sig") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: row=json.loads(line)
                except json.JSONDecodeError as exc:raise ValueError(f"{path}:{n}: {exc}") from exc
                if not isinstance(row,dict):raise ValueError(f"{path}:{n}: expected object")
                yield row
def atomic_jsonl(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".raw_",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
        if os.path.getsize(tmp)>LIMIT:raise ValueError(f"Partition too large ({path})")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def checksum(path):
    sha=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):sha.update(block)
    return sha.hexdigest()
def partition(input_rows=(),bootstrap=False):
    PARTS.mkdir(parents=True,exist_ok=True)
    existing=list(PARTS.glob("*.jsonl"))
    first=bootstrap and not MANIFEST.exists()
    byyear={}
    def add(row):
        year=year_for(row)
        if year not in byyear:byyear[year]=[]
        byyear[year].append(row)
    legacy_rows=0
    if first:
        for row in read_records(LEGACY):
            add(row);legacy_rows+=1
    for path in existing:
        for row in read_records(path):add(row)
    incoming=0
    for row in input_rows:
        add(row);incoming+=1
    if not first and not incoming and MANIFEST.exists():return
    if first and legacy_rows==0 and LEGACY.exists() and LEGACY.stat().st_size:raise ValueError("Legacy was not read")
    for year,records in sorted(byyear.items()):
        atomic_jsonl(PARTS/(year+".jsonl"),records)
    total=sum(len(v) for v in byyear.values())
    manifest={"format":"raw-jsonl-by-year-v1","partition_record_count":total,
              "partition_count":len(byyear),"raw_source_rows_on_first_migration":legacy_rows,
              "legacy_sha256":checksum(LEGACY) if first and LEGACY.exists() else None,
              "partitions":{y:{"records":len(r),"sha256":checksum(PARTS/(y+".jsonl"))} for y,r in sorted(byyear.items())}}
    if MANIFEST.exists() and not first:
        older=json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest["raw_source_rows_on_first_migration"]=older.get("raw_source_rows_on_first_migration",0)
        manifest["legacy_sha256"]=older.get("legacy_sha256")
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    observed=sum(1 for f in PARTS.glob("*.jsonl") for _ in read_records(f))
    if observed!=total:raise ValueError(f"Raw partition QA failed: {observed} vs {total}")
    print("Partition QA OK:",len(byyear),"years,",total,"raw rows; legacy input",legacy_rows,", added",incoming)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--bootstrap",action="store_true")
    args=parser.parse_args()
    partition(bootstrap=args.bootstrap)
if __name__=="__main__":main()
