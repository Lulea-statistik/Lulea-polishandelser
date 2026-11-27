#!/usr/bin/env python3
"""Read-only candidate audit; no changes to published classifications."""
import csv
import re
import unicodedata
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
ROAD = re.compile(r"(?<![a-z0-9])(?:e\s*\d{1,3}|(?:riksva[g]|lansva[g]|vag(?:en)?|rv|lv)\s*(?:nr\.?\s*)?\d{1,4}|[a-z]{3,}(?:vagen|leden|gatan|bron|banken))(?![a-z0-9])")
GENERIC = {"motorvagen","landsvagen","grusvagen","cykelvagen","gangvagen","ater vandsgatan","atervandsgatan","huvudleden","riksvagen","lansvagen","bilvagen","omvagen","vagen","gatan","bron","trottoaren"}
places = {unicodedata.normalize("NFC",r["place_name"]).casefold():r["place_name"] for r in read("data/norrbotten_place_to_municipality.csv") if r.get("municipality")=="Luleå" and clean(r["place_name"])!="lulea"}
place_patterns = {p:re.compile(r"(?<!\w)"+re.escape(p)+r"(?!\w)") for p in places}
def roads(s):
    found=set()
    for m in ROAD.finditer(clean(s)):
        v=m.group()
        if v=="gaddviksbron":
            prefix=clean(s)[:m.start()]
            qualifier=re.search(r"\b(gamla|nya)\s+$",prefix)
            if qualifier:v=qualifier.group(1)+" "+v
        if v in GENERIC: continue
        if re.fullmatch(r"e\s*\d+",v): v=v.replace(" ","").upper()
        elif re.search(r"\d+$",v): v="Väg "+re.search(r"\d+$",v).group()
        found.add(v)
    return found
def areas(s):
    raw=unicodedata.normalize("NFC",s or "").casefold()
    s=clean(s)
    return {name for name,pats in PATTERNS.items() if any(p.search(s) for p in pats)} | {places[p] for p,pat in place_patterns.items() if pat.search(raw)}
def serialize(s): return " | ".join(sorted(s))
events=read("data/events.csv")
details=read("data/summary_details_dedup.csv")
parsed={str(r.get("parent_event_id","")).strip() for r in details}
# Importing expanded builder would rewrite published files; reproduce only its
# narrow explicit-place exceptions and inclusion criteria.
from build_lulea_districts import ROAD_PATTERNS, district_dispatch_evidence
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

# Group 3: new names are hypotheses, not a verified locality registry.
NEW_NAMES=("Jämtön","Strömsund","Börjelslandet","Niemisel","Smedsbyn","Sinksundet","Kallviken","Orrbyn","Högsta","Örarna")
def new_names(text):
    raw=unicodedata.normalize("NFC",text or "").casefold()
    return {name for name in NEW_NAMES if re.search(r"(?<!\w)"+re.escape(name.casefold())+r"(?!\w)",raw)}
def context_role(sentence):
    n=clean(sentence)
    # These are linguistic review tags, not proof of event location.
    if re.search(r"\b(?:till|fran|mot|mellan|via|i riktning mot|pa vag till|pa vag fran)\b",n):return "fardvag eller riktning – granska"
    if re.search(r"\b(?:sjukhus|fors till|fordes till|hemadress|bosatt|anmalare|tidigare|senare)\b",n):return "annan kontext – granska"
    if re.search(r"\b(?:larm|olycka|kollision|kontroll|brand|inbrott|misshandel|stold|stopp|patrull|paf(f)?ades)\w*\b",n) and re.search(r"\b(?:i|pa|vid|intill|utanfor|kring|langs)\b",n):return "mojlig handelseplats – granska"
    return "oklar kontext – granska"
context_rows=[]
group3_rows=[]
def group3(series,kind,eid,location,narrative,rp,rt,ap,at):
    # Use one row per candidate event, several context rows per event.
    # Keep excerpts in restricted-lifetime Actions artifacts, never Pages.
    extra_place=new_names(location)
    extra_text=new_names(narrative)
    if extra_place: group="1 nya ortnamn i eget platsfalt"
    elif "Centrum" in at: group="2 Centrum i text"
    elif any(re.fullmatch(r"(?:E\d+|Väg \d+)",v) for v in rt):group="3 vagnummer i text"
    elif at and not rt:group="4 andra omraden i text"
    elif (rp or rt) and (ap or at):group="5 vag och omrade"
    else:group="6 ovriga konflikter"
    group3_rows.append(dict(series=series,source=kind,event_id=eid,group=group,new_place=serialize(extra_place),new_text=serialize(extra_text),road_place=serialize(rp),road_text=serialize(rt),area_place=serialize(ap),area_text=serialize(at)))
    # Split conservatively; punctuation and times can break sentence boundaries.
    # Limit to distinct snippets and retain source identity.
    seen_sentences=set()
    for sentence in re.split(r"(?<=[.!?])\s+|\r?\n+",narrative):
        sentence=" ".join(sentence.split())
        if not sentence or sentence in seen_sentences:continue
        seen_sentences.add(sentence)
        rs,ars,ns=roads(sentence),areas(sentence),new_names(sentence)
        if not (rs or ars or ns):continue
        # No automatic assignment; excerpt is for source review only.
        context_rows.append(dict(series=series,event_id=eid,source=kind,group=group,role=context_role(sentence),roads=serialize(rs),areas=serialize(ars),new_names=serialize(ns),excerpt=sentence[:500]))


# Co-occurrence is not a verified conflict. Preserve evidence separately from
# geographic decisions, including already classified events.
from build_lulea_districts import EXACT_LOCALITIES, NARRATIVE_DISTRICT_NAMES, CENTRUM_OBJECTS
named_areas={name:{name} for name in NARRATIVE_DISTRICT_NAMES}
named_areas["Centrum"]={x for x in CENTRUM_OBJECTS if x not in ("centrum","busstation","busstationen","jarnvagsstation","jarnvagsstationen")}
for name in EXACT_LOCALITIES:named_areas[name]={name}
# Use exact Unicode for actual place names; normalized variants only for
# Centrum labels defined in the existing normalized vocabulary.
def independent_areas(s):
    raw=unicodedata.normalize("NFC",s or "").casefold()
    result=set(new_names(s))
    for name,names in named_areas.items():
        hay=clean(s) if name=="Centrum" else raw
        for alias in names:
            needle=clean(alias) if name=="Centrum" else alias.casefold()
            if re.search(r"(?<!\w)"+re.escape(needle)+r"(?!\w)",hay):
                result.add(name)
                break
    return result
def numbered(s):
    return {x for x in roads(s) if re.fullmatch(r"(?:E\d+|Väg \d+)",x)}
from road_area_segment_gate import segment_reason, local_evidence
pair_events=[]
pair_counts=Counter()
rejected_pairs=[]
shared_places=Counter((str(r.get('parent_event_id','')).strip(),clean(r.get('place_text') or '')) for r in details if (r.get('place_text') or '').strip())
def pair_audit(series,kind,eid,geo,location,narrative):
    if kind=="ej uppdelad sammanfattning":return
    rp,rt=numbered(location),numbered(narrative)
    ap,at=independent_areas(location),independent_areas(narrative)
    if not (rp|rt) or not (ap|at):return
    parent=eid.split(':',1)[0] if kind=='underhändelse' else eid
    reason=segment_reason(location,narrative,numbered,independent_areas,shared_place=(kind=='underhändelse' and shared_places[(parent,clean(location))]>1 and len(location)>120),parsed_parent=(kind=='notis' and eid in parsed))
    # The pairs are review hypotheses, not all asserted event locations.
    sentences=[" ".join(x.split()) for x in re.split(r"(?<=[.!?])\s+|\r?\n+",narrative) if x.strip()]
    for road in sorted(rp|rt):
        for area in sorted(ap|at):
            same=[x for x in sentences if road in numbered(x) and area in independent_areas(x)]
            if road in rp and area in ap: evidence="båda i eget platsfält"
            elif same:evidence="samma mening"
            elif road in rp or area in ap:evidence="platsfält och text"
            else:evidence="separata textomnämnanden"
            # Rutvik/97 is explicitly raised by the user, not a GIS-verified
            # incompatibility; prioritize review rather than silently recode.
            priority="särskild kontroll: Rutvik/väg 97" if (road,area)==("Väg 97","Rutvik") else "granska"
            context=" | ".join(dict.fromkeys(same))[:600]
            if not context:
                context=" | ".join(dict.fromkeys(x for x in sentences if road in numbered(x) or area in independent_areas(x)))[:600]
            record=dict(series=series,source=kind,event_id=eid,current_area=geo,road=road,area=area,evidence=evidence,priority=priority,location=location,excerpt=context)
            reject=reason or ('' if local_evidence(location,narrative,road,area,numbered,independent_areas) else 'ingen lokal gemensam platsuppgift')
            if reject:
                rejected_pairs.append(dict(record,reason=reject))
                continue
            pair_events.append(record)
            pair_counts[(series,road,area,evidence,geo!=UNKNOWN)]+=1

rows=[]
dispatch_review=[]
baseline=Counter()
def audit(series,kind,eid,r,geo,location,narrative):
    baseline[(series,"total")]+=1
    if not yes(r.get("is_summary")):pair_audit(series,kind,eid,geo,location,narrative)
    if geo!=UNKNOWN:
        candidate=dict(r) if kind=="notis" else {"title_location":location,"description":narrative}
        evidence=district_dispatch_evidence(candidate) if kind!="ej uppdelad sammanfattning" else None
        if evidence and evidence[0]==geo:
            dispatch_review.append(dict(series=series,event_id=eid,source=kind,area=geo,excerpt=evidence[1]))
        return
    baseline[(series,"unknown")]+=1
    rp,rt=roads(location),roads(narrative)
    ap,at=areas(location),areas(narrative)
    # Road hits already represented in the road series cannot be identified
    # from the public monthly aggregate. Do not count them as new.
    if len(rp)==1 and not (rt-rp) and not ap and not at: status="en väg i eget platsfält"
    elif len(ap)==1 and not (at-ap) and not rp and not rt: status="ett område i eget platsfält"
    elif rp or rt or ap or at: status="textledtråd eller konflikt – granska"
    else: status="inga matchade ledtrådar"
    if status=="textledtråd eller konflikt – granska":group3(series,kind,eid,location,narrative,rp,rt,ap,at)
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

# All group 3 events accounted for, without changing classifications.
assert len(group3_rows)==sum(n for (series,status),n in counts.items() if status=="textledtråd eller konflikt – granska")
def export(name,records,fields):
    with (OUT/name).open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
export("group3_events.csv",group3_rows,["series","source","event_id","group","new_place","new_text","road_place","road_text","area_place","area_text"])
export("group3_context.csv",context_rows,["series","event_id","source","group","role","roads","areas","new_names","excerpt"])
freq=Counter((r["series"],r["group"]) for r in group3_rows)
roles=Counter((r["series"],r["group"],r["role"]) for r in context_rows)
newfreq=Counter((r["series"],name) for r in group3_rows for name in r["new_place"].split(" | ") if name)
report=["# Grupp 3 – kontextrevision","","Prioriteringsgrupper är ömsesidigt uteslutande. Meningsroller är heuristiska och kan överlappa per händelse. Nya ortnamn är ej verifierade.",""]
for series in ("original","expanded"):
    report += [f"## {series}", *[f"- {group}: {n}" for (ss,group),n in sorted(freq.items()) if ss==series], "", "Nya ortnamn i eget platsfält:", *[f"- {name}: {n}" for (ss,name),n in newfreq.most_common() if ss==series], "", "Kontextroller (meningar, ej unika händelser):", *[f"- {group} / {role}: {n}" for (ss,group,role),n in sorted(roles.items()) if ss==series], ""]
(OUT/"group3_summary.md").write_text("\n".join(report),encoding="utf-8")
print("\n".join(report))

export("dispatch_review.csv",dispatch_review,["series","event_id","source","area","excerpt"])

export("road_area_pairs.csv",pair_events,["series","source","event_id","current_area","road","area","evidence","priority","location","excerpt"])
export("road_area_pair_counts.csv",[dict(series=s,road=r,area=a,evidence=e,already_area_classified=k,count=n) for (s,r,a,e,k),n in sorted(pair_counts.items())],["series","road","area","evidence","already_area_classified","count"])
summary=["# Väg och område – samexistensrevision","","Inga klassificeringar ändrade. Samförekomst är inte bevis för konflikt eller geografisk förenlighet. Endast vägnummer och självständiga områdesomnämnanden; inga gatunamnsinferenser. Osplittrade sammanfattningar undantas.",""]
for series in ("original","expanded"):
    subset=[x for x in pair_events if x["series"]==series]
    unique={(x["source"],x["event_id"]) for x in subset}
    known={(x["source"],x["event_id"]) for x in subset if x["current_area"]!=UNKNOWN}
    combos=Counter((x["road"],x["area"]) for x in subset)
    summary += [f"## {series}",f"- Unika kandidathändelser: {len(unique)}",f"- Redan områdesklassificerade: {len(known)}",f"- Okänt delområde: {len(unique-known)}",f"- Unika väg/områdespar: {len(combos)}",f"- Rutvik/väg 97: {combos[('Väg 97','Rutvik')]}", "", "Vanligaste kombinationer:", *[f"- {r} / {a}: {n}" for (r,a),n in combos.most_common(30)],""]
(OUT/"road_area_summary.md").write_text("\n".join(summary),encoding="utf-8")
print("\n".join(summary))

export("road_area_segment_excluded.csv",rejected_pairs,["series","source","event_id","current_area","road","area","evidence","priority","location","excerpt","reason"])
seg=["# Segmentkontroll – före och efter","","Före = samma underlag med tidigare samförekomstmetod. Efter = konservativ granskningskö, inte verifierade geografier. Uteslutna kandidater sparas separat; ingen publicerad statistik ändras.",""]
for series in ("original","expanded"):
    kept=[r for r in pair_events if r["series"]==series]
    dropped=[r for r in rejected_pairs if r["series"]==series]
    ids=lambda rr:{(r["source"],r["event_id"]) for r in rr}
    seg += [f"## {series}",f"- Händelser före: {len(ids(kept+dropped))}; efter: {len(ids(kept))}",f"- Händelse/par-rader före: {len(kept)+len(dropped)}; efter: {len(kept)}",f"- E45/Råneå före: {sum(r['road']=='E45' and r['area']=='Råneå' for r in kept+dropped)}; efter: {sum(r['road']=='E45' and r['area']=='Råneå' for r in kept)}",*[f"- Uteslutna par: {reason}: {n}" for reason,n in Counter(r["reason"] for r in dropped).most_common()],""]
(OUT/"road_area_segment_summary.md").write_text("\n".join(seg),encoding="utf-8")
print("\n".join(seg))


# User-reviewed shortlist, not an authoritative polygon intersection table.
REVIEWED_PAIRS={("E4","Rutvik"),("E4","Persön"),("Väg 97","Sunderbyn"),("E4","Jämtön"),("E4","Strömsund"),("Väg 94","Klöverträsk"),("Väg 383","Smedsbyn"),("E4","Börjelslandet"),("Väg 596","Sinksundet"),("Väg 616","Bälinge")}
def placement_review(row):
    text=clean(row["location"]+" "+row["excerpt"])
    area=clean(row["area"])
    # Retain proximity and direction separately from an explicit location.
    if re.search(r"\b(?:\d+(?:[.,]\d+)?\s*(?:km|mil|meter|m)\s+)?(?:norr|soder|oster|vaster)\s+om\s+(?:norra |sodra )?"+re.escape(area)+r"\b",text) or re.search(r"\b(?:mellan|mot|fran|strax fore|strax efter)\b[^.!?]{0,80}\b"+re.escape(area)+r"\b",text):
        return "riktning eller avstand – ej områdestilldelning"
    if re.search(r"\b(?:i hojd med|i trakten av|i narheten av|utanfor|vid)\s+(?:norra |sodra )?"+re.escape(area)+r"\b",text):
        return "närhet – ej verifierad områdesgräns"
    if re.search(r"\b(?:tidigare|senare|fordes|transporterades|avstangd|avstangning|omledning|avakningarna|flera olyckor)\b",text):
        return "övrig kontext – manuell kontroll"
    road=(r"e\s*"+row["road"][1:] if row["road"].startswith("E") else r"(?:riksvag|lansvag|vag(?:en)?|rv|lv)\s*(?:nr\.?\s*)?"+row["road"].split()[-1])
    name=r"(?:norra |sodra )?"+re.escape(area)
    direct=re.compile(r"(?<![a-z0-9])"+road+r"(?![0-9])\s*(?:,\s*|\s+)(?:i\s+)?"+name+r"(?![a-z])")
    reverse=re.compile(r"(?<![a-z])"+name+r"(?![a-z])\s+(?:pa\s+)?"+road+r"(?![0-9])")
    if direct.search(text) or reverse.search(text):
        return "explicit väg–ort – granska händelseplats"
    return "övrig kontext – manuell kontroll"
placement=[]
for row in pair_events:
    if row["series"]!="expanded" or (row["road"],row["area"]) not in REVIEWED_PAIRS:continue
    placement.append(dict(row,placement=placement_review(row)))
export("road_area_placement_review.csv",placement,["series","source","event_id","current_area","road","area","evidence","priority","location","excerpt","placement"])
report=["# Väg–ort: individuell platsbedömning","","Användarbedömd lista med tio väg–ortskopplingar. Automatisk språklig prioritering, inte bevis för stadsdelstillhörighet. Ingen ändring av klassificeringar.",""]
for state in ("okänt","befintligt"):
    subset=[r for r in placement if (r["current_area"]==UNKNOWN)==(state=="okänt")]
    report += [f"## {state}: {len(subset)} händelser",*[f"- {k}: {n}" for k,n in Counter(r["placement"] for r in subset).most_common()],""]
(OUT/"road_area_placement_summary.md").write_text("\n".join(report),encoding="utf-8")
print("\n".join(report))
