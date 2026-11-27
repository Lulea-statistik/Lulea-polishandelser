#!/usr/bin/env python3
"""Read-only candidate audit; no changes to published classifications."""
import csv
import re
from collections import Counter
from pathlib import Path
from build_lulea_districts import district, normalize, UNKNOWN, PATTERNS
from build_expanded_monthly import admin_non_event, NO_NEW_EVENT_RE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit-output"
OUT.mkdir(exist_ok=True)
def read(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
def yes(v):
    return str(v or "").strip().casefold() in ("true", "1")
def valid(r):
    return r.get("geography_group","").strip()=="Luleå kommun" and str(r.get("year","")).isdigit() and str(r.get("month","")).isdigit() and 1<=int(r["month"])<=12
def clean(s):
    return normalize(s).strip()
# Only the event's own location fields and its own text.
ROAD = re.compile(r"(?<![a-z0-9])(?:e\s*\d{1,3}|(?:riksva[g]|lansva[g]|vag(?:en)?|rv)\s*(?:nr\.?\s*)?\d{1,4}|[a-z]{3,}(?:vagen|leden|gatan|bron|banken))(?![a-z0-9])")
GENERIC = {"motorvagen","landsvagen","grusvagen","cykelvagen","gangvagen","ater vandsgatan","atervandsgatan","huvudleden","riksvagen","lansvagen","bilvagen","omvagen","vagen","gatan","bron","trottoaren"}
places = {clean(r["place_name"]):r["place_name"] for r in read("data/norrbotten_place_to_municipality.csv") if r.get("municipality")=="Luleå" and clean(r["place_name"])!="lulea"}
place_patterns = {p:re.compile(r"(?<![a-z])"+re.escape(p)+r"(?![a-z])") for p in places}
def roads(s):
    found=set()
    for m in ROAD.finditer(clean(s)):
        v=m.group()
        if v in GENERIC: continue
        if re.fullmatch(r"e\s*\d+",v): v=v.replace(" ","").upper()
        elif re.search(r"\d+$",v): v="Väg "+re.search(r"\d+$",v).group()
        found.add(v)
    return found
def areas(s):
    s=clean(s)
    return {name for name,pats in PATTERNS.items() if any(p.search(s) for p in pats)} | {places[p] for p,pat in place_patterns.items() if pat.search(s)}
def serialize(s): return " | ".join(sorted(s))
events=read("data/events.csv")
details=read("data/summary_details_dedup.csv")
parsed={str(r.get("parent_event_id","")).strip() for r in details}
# Importing expanded builder would rewrite published files; reproduce only its
# narrow explicit-place exceptions and inclusion criteria.
from build_lulea_districts import ROAD_PATTERNS
def subdistrict(r):
    place=r.get("place_text") or ""
    desc=r.get("description") or ""
    current=district({"title_location":place,"description":desc})
    if current!=UNKNOWN:return current
    target={"centrala luleå":"Centrum","skutvikens industriområde":"Skutviken"}.get(place.strip().casefold())
    if not target:return current
    n=clean(desc)
    if any(k!=target and any(p.search(n) for p in pats) for k,pats in PATTERNS.items()) or any(p.search(n) for p in ROAD_PATTERNS):return UNKNOWN
    return target
rows=[]
baseline=Counter()
def audit(series,kind,eid,r,geo,location,narrative):
    baseline[(series,"total")]+=1
    if geo!=UNKNOWN:return
    baseline[(series,"unknown")]+=1
    rp,rt=roads(location),roads(narrative)
    ap,at=areas(location),areas(narrative)
    # Road hits already represented in the road series cannot be identified
    # from the public monthly aggregate. Do not count them as new.
    if len(rp)==1 and not (rt-rp) and not ap and not at: status="en väg i eget platsfält"
    elif len(ap)==1 and not (at-ap) and not rp and not rt: status="ett område i eget platsfält"
    elif rp or rt or ap or at: status="textledtråd eller konflikt – granska"
    else: status="inga matchade ledtrådar"
    rows.append(dict(series=series,source=kind,event_id=eid,year=r.get("year"),month=r.get("month"),event_type=r.get("event_type_extracted") or r.get("type_original"),status=status,road_place=serialize(rp),road_text=serialize(rt),area_place=serialize(ap),area_text=serialize(at),location=location))
seen=set()
for r in events:
    if not valid(r):continue
    eid=str(r.get("event_id","")).strip()
    if eid and eid in seen:continue
    if eid:seen.add(eid)
    loc=" | ".join(r.get(k) or "" for k in ("title_location","location_string"))
    text=" ".join(r.get(k) or "" for k in ("headline","description","content"))
    geo=district(r)
    audit("original","notis",eid,r,geo,loc,text)
    if yes(r.get("is_summary")):
        if eid in parsed or NO_NEW_EVENT_RE.search(text):continue
        # Unsplit summary can be audited but never proposed as an individual place.
        audit("expanded","ej uppdelad sammanfattning",eid,r,geo,"","")
    elif not admin_non_event(r):
        audit("expanded","notis",eid,r,geo,loc,text)
for i,r in enumerate(details):
    if not valid(r) or not yes(r.get("include_as_extra")):continue
    audit("expanded","underhändelse",str(r.get("parent_event_id",""))+":"+str(i),r,subdistrict(r),r.get("place_text") or "",r.get("description") or "")
assert baseline[("expanded","total")]>0 and baseline[("original","total")]>0
# Compare against published snapshots; fail if classification logic diverges.
for series,path in [("original","docs/data/lulea_district_monthly.csv"),("expanded","docs/data/lulea_district_expanded_monthly.csv")]:
    pub=read(path)
    expected=sum(int(r["event_count"]) for r in pub if r["geography_group"]==UNKNOWN)
    total=sum(int(r["event_count"]) for r in pub)
    assert (baseline[(series,"unknown")],baseline[(series,"total")])==(expected,total), f"{series}: source and published snapshot differ; rebuild baseline before interpreting"
fields=list(rows[0]) if rows else ["series","status"]
with (OUT/"candidates.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
counts=Counter((r["series"],r["status"]) for r in rows)
terms=Counter((r["series"],field,term) for r in rows for field in ("road_place","road_text","area_place","area_text") for term in r[field].split(" | ") if term)
with (OUT/"frequencies.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f);w.writerow(["series","source_field","candidate","count"])
    for (series,field,term),n in terms.most_common():w.writerow([series,field,term,n])
lines=["# Luleå – revision av okänt delområde","","Inga geografier ändrade. Kandidater är inte verifierade nya träffar; vägar kan redan ingå i väggeografin.",""]
for series in ("original","expanded"):
    lines += [f"## {series}",f"Totalt: {baseline[(series,'total')]}; okänt delområde: {baseline[(series,'unknown')]}",* [f"- {status}: {n}" for (s,status),n in counts.items() if s==series],""]
(OUT/"summary.md").write_text("\n".join(lines),encoding="utf-8")
print("\n".join(lines))
