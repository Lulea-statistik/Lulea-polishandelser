"""Audit left-to-right place fields without changing any geographic classification."""
from __future__ import annotations
from pathlib import Path
import re
import unicodedata
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
OUT=DATA/"place_order_audit.csv"
STATS=DATA/"place_order_audit_stats.csv"
UNKNOWN=DATA/"place_order_unknown_candidates.csv"
GENERIC={"norrbotten","norrbottens lan","sverige","norrland","norrbottens kommun"}

def norm(x):
    s=unicodedata.normalize("NFKD",str(x or "").casefold())
    s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 -]"," ",s)).strip()

def first_part(value):
    return str(value or "").split(",",1)[0].strip()

def main():
    events=pd.read_csv(DATA/"events.csv",dtype=str,keep_default_na=False,low_memory=False)
    places=pd.read_csv(DATA/"norrbotten_place_to_municipality.csv",dtype=str,keep_default_na=False)
    names={}
    for _,r in places.iterrows():
        n=norm(r["place_name"])
        if n and len(n)>=4 and n not in GENERIC:
            names.setdefault(n,set()).add(r["municipality"])
    official={k:next(iter(v)) for k,v in names.items() if len(v)==1}
    ordinary=events[~events.is_summary.str.casefold().isin(["true","1"])].copy()
    ordinary["first_part"]=ordinary.location_string.map(first_part)
    ordinary["first_norm"]=ordinary.first_part.map(norm)
    ordinary["proposed"]=ordinary.first_norm.map(official).fillna("")
    ordinary["is_known_api"]=ordinary.municipality_source.eq("api") & ordinary.municipality.ne("")
    gold=ordinary[ordinary.is_known_api]
    matched=gold[gold.proposed.ne("")]
    correct=int((matched.proposed==matched.municipality).sum())
    wrong=int(len(matched)-correct)
    # Only the API-classified events form an independent validation reference.
    unknown=ordinary[ordinary.geography_group.eq("Norrbotten, okänd kommun")]
    candidates=unknown[unknown.proposed.ne("")].copy()
    # A county reference is not evidence if another municipality or county is mentioned.
    county_conflict=re.compile(r"västerbotten|västernorrland|jämtland|gävleborg|dalarna",re.I)
    candidates=candidates[~candidates.location_string.str.contains(county_conflict,na=False)]
    candidates=candidates[~candidates.title_location.str.contains(county_conflict,na=False)]
    candidates["review_status"]="manual_review_required"
    candidates["evidence"]="first_component_matches_unambiguous_official_place_name"
    fields=["event_id","date","type_original","title_location","location_string",
        "first_part","proposed","headline","description","review_status","evidence"]
    candidates[fields].to_csv(UNKNOWN,index=False,encoding="utf-8")
    errors=matched[matched.proposed.ne(matched.municipality)]
    errors[["event_id","date","first_part","proposed","municipality","location_string",
        "headline"]].to_csv(OUT,index=False,encoding="utf-8")
    stats=[
        ("ordinary_rows",len(ordinary)),("known_api",len(gold)),
        ("matched_api",len(matched)),("matched_api_correct",correct),
        ("matched_api_incorrect",wrong),
        ("precision_matched_api",f"{correct/len(matched):.5f}" if len(matched) else ""),
        ("unknown_ordinary",len(unknown)),("unknown_official_place_candidates",len(candidates)),
        ("auto_reclassified",0),
    ]
    pd.DataFrame(stats,columns=["metric","value"]).to_csv(STATS,index=False,encoding="utf-8")
    print(" ".join(f"{a}={b}" for a,b in stats))

if __name__=="__main__":
    main()
