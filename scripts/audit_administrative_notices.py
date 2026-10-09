"""Audit exclusions and still-included administrative notices. No statistics modified."""
from pathlib import Path
import re
import pandas as pd
from build_expanded_monthly import admin_non_event, truthy

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
events=pd.read_csv(DATA/"events.csv",dtype=str,keep_default_na=False,low_memory=False)
ordinary=events[~truthy(events["is_summary"])].copy()
excluded=ordinary[ordinary.apply(admin_non_event,axis=1)].copy()
included=ordinary[~ordinary.index.isin(excluded.index)].copy()
INCIDENT=re.compile(r"(?i)\b(?:trafikolycka|viltolycka|inbrott|misshandel|rån|stöld|"
    r"rattfylleri|skottlossning|försvunnen|gripen|patrull|larm|brottsmisstanke|"
    r"omhändertag|brand|anträffad|misstänkt)\b")
ADMIN=re.compile(r"(?i)(?:kommunikatör|obemannat|inga? (?:akuta |särskilda )?"
    r"(?:händelser|ärenden)|inget (?:särskilt )?att rapportera|"
    r"lugnt(?: under | på | i )|lugn (?:natt|morgon|kväll|dag)|"
    r"utan (?:några )?händelser|ingen (?:händelse|insats))")
def body(r): return " ".join(str(r.get(c,"")) for c in ["headline","description","content"])
excluded["review_text"]=excluded.apply(body,axis=1)
excluded["incident_language"]=excluded["review_text"].str.contains(INCIDENT,na=False)
excluded["review_flag"]=excluded["incident_language"].map({True:"potential_incident_check",False:"no_incident_keywords"})
excluded_cols=["event_id","date","type_original","headline","content","geography_group","review_flag"]
excluded[excluded_cols].to_csv(DATA/"excluded_administrative_review_full_text.csv",index=False,encoding="utf-8")
included=included[included.type_original.str.casefold().isin(["övrigt","tillfälligt obemannat"])].copy()
included["review_text"]=included.apply(body,axis=1)
potential=included[included["review_text"].str.contains(ADMIN,na=False)].copy()
potential["incident_language"]=potential["review_text"].str.contains(INCIDENT,na=False)
potential["review_flag"]=potential["incident_language"].map({True:"mixed_or_incident_check",False:"possible_admin_non_event"})
potential[excluded_cols].to_csv(DATA/"included_administrative_review_candidates.csv",index=False,encoding="utf-8")
stats=[("excluded_count",len(excluded)),("excluded_keyword_incident_check",int(excluded.incident_language.sum())),
("included_ovrigt_or_unstaffed",len(included)),("included_admin_candidates",len(potential)),
("included_admin_candidates_with_incident_words",int(potential.incident_language.sum())),
("auto_reclassified",0)]
pd.DataFrame(stats,columns=["metric","value"]).to_csv(DATA/"administrative_review_stats.csv",index=False)
print(" ".join(f"{a}={b}" for a,b in stats))
