from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EVENTS=ROOT/"data"/"events.csv"
OUT=ROOT/"data"/"place_reclassification_audit.csv"
SUMMARY=ROOT/"data"/"place_reclassification_summary.csv"

def main():
    df=pd.read_csv(EVENTS,dtype={"event_id":"string"},low_memory=False)
    x=df[df.get("municipality_source","").fillna("").astype(str).eq("place_dictionary")].copy()
    cols=["event_id","date","type_original","title_location","location_string","municipality","geography_group","municipality_source"]
    x[cols].to_csv(OUT,index=False,encoding="utf-8")
    s=(x.groupby("municipality",dropna=False).size().reset_index(name="event_count")
         .sort_values("event_count",ascending=False))
    s.to_csv(SUMMARY,index=False,encoding="utf-8")
    print(f"place_dictionary_reclassified={len(x)}")
    if not s.empty:
        print(s.to_string(index=False))

if __name__=="__main__":
    main()
