from __future__ import annotations

"""Precision-first review queue: never changes source geography automatically."""
import re
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EVENTS=ROOT/"data/events.csv"
DICTIONARY=ROOT/"data/norrbotten_place_to_municipality.csv"
OUT=ROOT/"data/unknown_municipality_text_review.csv"
STATS=ROOT/"data/unknown_municipality_text_review_stats.csv"

def normalize(value):
    import unicodedata
    s=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(c for c in s if not unicodedata.combining(c))

def main():
    df=pd.read_csv(EVENTS,dtype=str,keep_default_na=False)
    unknown=df[df.geography_group.eq("Norrbotten, okänd kommun")].copy()
    normal=unknown[~unknown.is_summary.str.casefold().isin(["true","1"])].copy()
    places=pd.read_csv(DICTIONARY,dtype=str).fillna("")
    byplace={}
    for _,p in places.iterrows():
        name=normalize(p["place_name"]).strip()
        if len(name)>=5 and p["municipality"]:
            byplace.setdefault(name,set()).add(p["municipality"])
    # Don't use names that belong to multiple municipalities, or generic words.
    byplace={name:next(iter(munis)) for name,munis in byplace.items() if len(munis)==1}
    blocked={"boden","kiruna","kalix","pitea","lulea","pajala","haparanda",
             "jokkmokk","gallivare","arjeplog","arvidsjaur","alvsbyn",
             "overkalix","overtornea"}
    byplace={k:v for k,v in byplace.items() if k not in blocked}
    hits=[]
    for _,r in normal.iterrows():
        # Search only the incident description, not source links or metadata.
        body=normalize(" ".join([r.get("description",""),r.get("content","")]))
        if not body.strip():
            continue
        strong={}
        for place,municipality in byplace.items():
            # Match an explicit incident location, not a casual mention.
            pat=r"\b(?:i|vid|pa|utanfor|nara|intill)\s+"+re.escape(place)+r"\b"
            if re.search(pat,body):
                strong.setdefault(municipality,set()).add(place)
        if len(strong)!=1:
            continue
        municipality=next(iter(strong))
        # Existing location field naming another municipality is contradictory.
        title=normalize(r.get("title_location",""))
        location=normalize(r.get("location_string",""))
        # No auto application: a person must verify each candidate.
        hits.append(dict(event_id=r.get("event_id",""),date=r.get("date",""),
            type_original=r.get("type_original",""),
            title_location=r.get("title_location",""),
            location_string=r.get("location_string",""),
            proposed_municipality=municipality,
            matching_places=" | ".join(sorted(strong[municipality])),
            excerpt=(r.get("description","")+" "+r.get("content",""))[:450],
            review_status="needs_manual_verification"))
    columns=["event_id","date","type_original","title_location","location_string",
             "proposed_municipality","matching_places","excerpt","review_status"]
    pd.DataFrame(hits,columns=columns).to_csv(OUT,index=False,encoding="utf-8")
    pd.DataFrame([
        ("unknown_total",len(unknown)),
        ("unknown_ordinary",len(normal)),
        ("unknown_summaries",len(unknown)-len(normal)),
        ("review_candidates",len(hits)),
        ("auto_reclassified",0),
    ],columns=["metric","value"]).to_csv(STATS,index=False)
    print(f"unknown_total={len(unknown)} ordinary={len(normal)} candidates={len(hits)} auto_reclassified=0")

if __name__=="__main__":
    main()
