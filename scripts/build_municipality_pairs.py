"""Produce auditable municipality-pair counts from event-level classifications.

Only explicit municipality_pair: sources are split. Do not guess at multi-city
identities when the source contains ambiguous_municipality_names.
"""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/events.csv"
OUT=ROOT/"data/norrbotten_municipality_pairs.csv"
COLUMNS=["year","municipality_combination","municipalities","event_count"]
df=pd.read_csv(SOURCE,dtype={"event_id":"string"},low_memory=False).fillna("")
group=df["geography_group"].astype(str).eq("Flera kommuner i Norrbotten")
rows=[]
for row in df.loc[group].to_dict("records"):
    source=str(row.get("municipality_source",""))
    if source.startswith("municipality_pair:"):
        names=sorted(set(x.strip() for x in source.split(":",1)[1].split("|") if x.strip()))
        if len(names)==2:
            combo=" + ".join(names)
        else:
            combo="Fler än två / otydlig kombination"
            names=[]
    else:
        combo="Fler än två / otydlig kombination"
        names=[]
    year=str(row.get("year","")).strip()
    if not year or year.lower()=="nan":continue
    rows.append({"year":year,"municipality_combination":combo,"municipalities":"|".join(names)})
if rows:
    result=(pd.DataFrame(rows).groupby(["year","municipality_combination","municipalities"],dropna=False)
            .size().reset_index(name="event_count")
            .sort_values(["year","event_count","municipality_combination"],ascending=[True,False,True]))
else:
    result=pd.DataFrame(columns=COLUMNS)
result.to_csv(OUT,index=False,encoding="utf-8")
print("Municipality groups:",len(rows),"pair rows:",sum(bool(x["municipalities"]) for x in rows),"summary rows:",len(result))
