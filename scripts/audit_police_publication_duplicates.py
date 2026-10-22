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

# Row-level review artifact. All source publication IDs remain available.
group_out=ROOT/"data/audit_police_publication_groups.csv"
from police_publication_dedup import normalized
review_rows=[]
for n,group in enumerate(groups,1):
    group_rows=[event_by_id[eid] for eid in group if eid in event_by_id]
    contents=[normalized(r.get("content")) for r in group_rows]
    distinct_texts=len(set(contents))
    for r in group_rows:
        content=normalized(r.get("content"))
        other=[x for x in contents if x!=content]
        review_rows.append({
            "group_id":f"G{n:03d}","group_size":len(group),"event_id":r.get("event_id",""),
            "date":r.get("date",""),"type_original":r.get("type_original",""),
            "headline":(r.get("headline") or "")[:300],
            "location_string":(r.get("location_string") or "")[:250],
            "content_length":len(content),
            "identical_content_in_group":"Ja" if distinct_texts==1 else "Nej",
            "content_preview":content[:650],
            "all_event_ids":" | ".join(group),
            "review_decision":"Ej granskad",
            "keep_as_canonical":"","reason":"",
        })
with group_out.open("w",encoding="utf-8",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=list(review_rows[0]) if review_rows else [
        "group_id","group_size","event_id","date","type_original","headline","location_string",
        "content_length","identical_content_in_group","content_preview","all_event_ids",
        "review_decision","keep_as_canonical","reason"])
    writer.writeheader();writer.writerows(review_rows)
print("Granskningstabell grupper:","grupper",len(groups),"publiceringar",len(review_rows))
print("Grupper med identisk löptext:",sum(len({normalized(event_by_id[eid].get("content")) for eid in group})==1 for group in groups))
print("Grupper med olika löptext:",sum(len({normalized(event_by_id[eid].get("content")) for eid in group})>1 for group in groups))
