#!/usr/bin/env python3
"""Generate conservative candidate review for all Lulea police publications."""
import csv
from pathlib import Path
from police_publication_dedup import candidate_pairs, REPLACED_BY

ROOT=Path(__file__).resolve().parents[1]
with (ROOT/"data/events.csv").open(encoding="utf-8-sig",newline="") as stream:
    events=[r for r in csv.DictReader(stream) if (r.get("geography_group") or "").strip()=="Luleå kommun"]
out=ROOT/"data/audit_police_publication_duplicates.csv"
candidates=list(candidate_pairs(events))
with out.open("w",encoding="utf-8",newline="") as stream:
    columns=["date","type_original","event_id_a","event_id_b","headline_similarity","a_shorter_content","review_status"]
    writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(candidates)
print("Allmän dubblettrevision, kandidater för manuell prövning:",len(candidates))
print("Bekräftade uppdateringspar:",REPLACED_BY)
for candidate in candidates[:35]:
    print("DUPLICATE_CANDIDATE",candidate["event_id_a"],candidate["event_id_b"],candidate["date"])

# Connected components avoid counting three pairwise matches as three incidents.
parent={}
def find(x):
    parent.setdefault(x,x)
    if parent[x]!=x:parent[x]=find(parent[x])
    return parent[x]
for r in candidates:
    a,b=r["event_id_a"],r["event_id_b"]
    parent[find(a)]=find(b)
groups={}
for eid in parent:
    groups.setdefault(find(eid),set()).add(eid)
groups=sorted((sorted(ids,key=lambda x:int(x) if x.isdigit() else x) for ids in groups.values()),key=lambda g:(-len(g),g[0]))
print("Dubblettkandidatgrupper:",len(groups))
print("Storlek per grupp:",{n:sum(len(g)==n for g in groups) for n in sorted({len(g) for g in groups})})
event_by_id={str(r.get("event_id") or "").strip():r for r in events}
for group in groups[:20]:
    print("DUPLICATE_GROUP",",".join(group)," | ".join(
        f"{eid}: "+str(event_by_id[eid].get("date") or "")+" / "+
        str(event_by_id[eid].get("headline") or "")[:110]+" / text_len="+str(len(event_by_id[eid].get("content") or ""))
        for eid in group if eid in event_by_id))
