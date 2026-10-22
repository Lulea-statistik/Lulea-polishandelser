#!/usr/bin/env python3
"""Generate conservative candidate review for all Lulea police publications."""
import csv
from pathlib import Path
from police_publication_dedup import candidate_pairs, REPLACED_BY, prohibited_merge

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

# Summary notices may contain multiple independently countable subevents.
def summary_notice(row):
    heading=normalized(row.get("headline") or "")
    typ=normalized(row.get("type_original") or "")
    return str(row.get("is_summary") or "").lower() in ("true","1") or "sammanfattning" in typ or any(
        term in heading for term in ("urval av nattens", "urval av kvallens", "nattens handelser", "polisverksamhet")
    )

def group_warning(group):
    rr=[event_by_id[eid] for eid in group if eid in event_by_id]
    if any(prohibited_merge(a,b) for a in group for b in group if a!=b):
        return "Verifierat separata händelser – slå inte ihop"
    if any(summary_notice(row) for row in rr):
        return "Sammanfattning – kontrollera nytillkomna underhändelser"
    return "Manuell verifiering krävs"

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
            "review_decision":group_warning(group),
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

# Prioritise review without turning textual identity into automatic dedup.
priority_out=ROOT/"data/audit_police_duplicate_review_priority.csv"
priorities=[]
for n,group in enumerate(groups,1):
    rr=[event_by_id[eid] for eid in group if eid in event_by_id]
    identical=len({normalized(r.get("content")) for r in rr})==1
    has_geo=len({normalized(r.get("location_string")) for r in rr})>1
    transport=any(any(x in normalized(r.get("type_original")+" "+(r.get("headline") or "")) for x in ("trafik","olycka","rattfylleri")) for r in rr)
    already_reviewed=set(group)=={"107404","107414"}
    if already_reviewed:
        review_priority="Redan verifierad"
    elif any(prohibited_merge(a,b) for a in group for b in group if a!=b):
        review_priority="Skyddad – separata händelser"
    elif any(summary_notice(r) for r in rr):
        review_priority="Hög – sammanfattning"
    elif has_geo:
        review_priority="Hög – geografisk skillnad"
    elif not identical:
        review_priority="Hög – uppdaterad text"
    else:
        review_priority="Medel – identisk text"
    priorities.append({"group_id":f"G{n:03d}","event_ids":" | ".join(group),
        "number_of_publications":len(group),
        "text_relation":"Identisk löptext" if identical else "Textskillnader",
        "different_location_fields":"Ja" if has_geo else "Nej",
        "transport_related":"Ja" if transport else "Nej",
        "review_priority":review_priority,
        "review_decision":"Verifierad sammanslagning" if already_reviewed else group_warning(group)})
with priority_out.open("w",encoding="utf-8",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=list(priorities[0]) if priorities else [
       "group_id","event_ids","number_of_publications","text_relation",
       "different_location_fields","transport_related","review_priority","review_decision"])
    writer.writeheader();writer.writerows(priorities)
from collections import Counter
print("Prioriteringsklasser:",dict(Counter(r["review_priority"] for r in priorities)))

# Compact source-text comparison for changed groups, including location mentions.
from difflib import SequenceMatcher
diff_out=ROOT/"data/audit_police_duplicate_text_differences.csv"
diff_rows=[]
for n,group in enumerate(groups,1):
    rr=[event_by_id[eid] for eid in group if eid in event_by_id]
    bodies=[normalized(r.get("content")) for r in rr]
    if len(set(bodies))<2:continue
    base=min(rr,key=lambda r:len(normalized(r.get("content"))))
    base_text=normalized(base.get("content"))
    for r in rr:
        if r is base:continue
        candidate=normalized(r.get("content"))
        # Compare full words, not characters: character fragments falsely suggest
        # unrelated incidents share updated facts.
        base_words=base_text.split()
        candidate_words=candidate.split()
        matcher=SequenceMatcher(None,base_words,candidate_words,autojunk=False)
        added=" | ".join(" ".join(candidate_words[j1:j2]) for tag,i1,i2,j1,j2 in matcher.get_opcodes() if tag in ("insert","replace")).strip()
        removed=" | ".join(" ".join(base_words[i1:i2]) for tag,i1,i2,j1,j2 in matcher.get_opcodes() if tag in ("delete","replace")).strip()
        diff_rows.append({
          "group_id":f"G{n:03d}","base_event_id":base.get("event_id",""),
          "compared_event_id":r.get("event_id",""),
          "date":r.get("date",""),"headline":r.get("headline","")[:250],
          "location_string_base":base.get("location_string","")[:180],
          "location_string_compared":r.get("location_string","")[:180],
          "base_length":len(base_text),"compared_length":len(candidate),
          "added_or_replaced_excerpt":added[:900],
          "removed_or_replaced_excerpt":removed[:500],
          "review_decision":"Ej granskad"})
with diff_out.open("w",encoding="utf-8",newline="") as stream:
    columns=["group_id","base_event_id","compared_event_id","date","headline",
       "location_string_base","location_string_compared","base_length","compared_length",
       "added_or_replaced_excerpt","removed_or_replaced_excerpt","review_decision"]
    writer=csv.DictWriter(stream,fieldnames=columns)
    writer.writeheader();writer.writerows(diff_rows)
print("Förändrade textjämförelser:",len(diff_rows))
for r in diff_rows[:15]:
    print("TEXT_DIFF_REVIEW",r["base_event_id"],r["compared_event_id"],repr(r["headline"][:90]),repr(r["added_or_replaced_excerpt"][:350]),repr(r["removed_or_replaced_excerpt"][:140]))

# Human-reviewed triage notes. These are not production dedup decisions.
triage_out=ROOT/"data/review_police_duplicate_text_cases.csv"
triage=[
 ("105825 | 105831 | 105832","Stark kandidat – granska full text","E4 Rönningen: one notice adds vehicle recovery; likely updated publication chain","Nej"),
 ("243612 | 243613","Separata händelser – skyddad grupp","Innerstaden woman vs Skutviken man; distinct incidents despite generic headline","Nej"),
 ("23232 | 23251","Risk för olika händelser","Different suspected offences and narrative; needs further source verification","Nej"),
 ("172103 | 172106","Sammanfattning – kontrollera underhändelser","A later night summary adds a quiet-period report; do not discard separately extracted incidents","Nej"),
 ("245223 | 245225","Sammanfattning – kontrollera underhändelser","Different detail level including assault report; inspect parent/child extraction","Nej"),
 ("251321 | 251346","Separata händelser – skyddad grupp","Different persons and alleged offences; prohibited_merge safeguard","Nej"),
 ("257284 | 257299","Separata händelser – skyddad grupp","Teenager and adult man in different narrative; prohibited_merge safeguard","Nej"),
 ("107404 | 107414","Verifierad sammanslagning","2019-02-14 same taxi-car crash with later 12:55 update; keep 107414","Ja"),
]
with triage_out.open("w",encoding="utf-8",newline="") as stream:
    writer=csv.writer(stream)
    writer.writerow(["event_ids","review_class","rationale","approved_for_dedup"])
    writer.writerows(triage)
print("Fördjupade granskningsfall:",len(triage),"varav redan verifierad sammanslagning:",sum(r[-1]=="Ja" for r in triage))

assert all(prohibited_merge(*pair) for pair in [("243612","243613"),("251321","251346"),("257284","257299")])
print("Skyddade separata händelsepar:",3)

print("Skyddade kandidatgrupper:",sum("Verifierat separata" in group_warning(group) for group in groups))
print("Sammanfattningsgrupper för underhändelsekontroll:",sum("Sammanfattning" in group_warning(group) for group in groups))

# Detail evidence for summary-group review; preserve every child/parent source.
summary_out=ROOT/"data/audit_police_summary_update_groups.csv"
summary_rows=[]
for n,group in enumerate(groups,1):
    rr=[event_by_id[eid] for eid in group if eid in event_by_id]
    if not any(summary_notice(r) for r in rr):continue
    for r in rr:
        eid=str(r.get("event_id") or "")
        narrative=normalized(r.get("content"))
        summary_rows.append({
            "group_id":f"G{n:03d}","event_id":eid,
            "date":r.get("date",""),"headline":r.get("headline",""),
            "location_string":r.get("location_string",""),
            "summary_flag":r.get("is_summary",""),
            "content_length":len(narrative),"content_excerpt":narrative[:1500],
            "requires_child_event_check":"Ja",
            "dedup_decision":"Ej beslutad"})
with summary_out.open("w",encoding="utf-8",newline="") as stream:
    cols=["group_id","event_id","date","headline","location_string","summary_flag","content_length","content_excerpt","requires_child_event_check","dedup_decision"]
    writer=csv.DictWriter(stream,fieldnames=cols);writer.writeheader();writer.writerows(summary_rows)
print("Sammanfattningspubliceringar att granska:",len(summary_rows))
for r in summary_rows:
    print("SUMMARY_REVIEW",r["group_id"],r["event_id"],repr(r["headline"][:90]),repr(r["content_excerpt"][:180]))
