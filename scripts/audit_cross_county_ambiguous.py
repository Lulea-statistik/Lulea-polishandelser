from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EVENTS=ROOT/"data"/"events.csv"
OUT=ROOT/"data"/"cross_county_ambiguous_audit.csv"

def main():
    df=pd.read_csv(EVENTS,dtype={"event_id":"string"},low_memory=False).fillna("")
    x=df[
        df["geography_group"].astype(str).eq("Norrbotten, okänd kommun")
        & df["municipality_source"].astype(str).eq("cross_county_ambiguous")
    ].copy()
    cols=["event_id","date","type_original","title_location","location_string",
          "administrative_area_level_1","municipality_source","geography_group"]
    x[cols].to_csv(OUT,index=False,encoding="utf-8")
    print(f"cross_county_ambiguous_rows={len(x)}")
    if len(x):
        print(x[cols].head(120).to_string(index=False))

if __name__=="__main__":
    main()
