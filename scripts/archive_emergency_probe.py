"""Keep a dated audit trail of SOS Alarm and Krisinformation reachability."""
from __future__ import annotations
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"data"
SRC=ROOT/"emergency_sources_probe.csv"
DST=ROOT/"emergency_sources_history.csv"
FIELDS=["checked_at","source","http_status","kind","item_count","fields","error"]
with SRC.open(encoding="utf-8",newline="") as file:
    probe=list(csv.DictReader(file))
history=[]
if DST.exists():
    with DST.open(encoding="utf-8",newline="") as file:
        history=list(csv.DictReader(file))
checked_at=datetime.now(timezone.utc).isoformat()
for row in probe:
    history.append({key:(checked_at if key=="checked_at" else row.get(key,"")) for key in FIELDS})
with DST.open("w",encoding="utf-8",newline="") as file:
    writer=csv.DictWriter(file,fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(history)
print("archived_checks=",len(probe),"history_rows=",len(history))
