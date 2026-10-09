from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
EVENTS=ROOT/"data"/"events.csv"
OUT=ROOT/"data"/"unknown_short_locations.csv"

def main():
    df=pd.read_csv(EVENTS,dtype={"event_id":"string"},low_memory=False).fillna("")
    x=df[
        df["geography_group"].astype(str).eq("Norrbotten, okänd kommun")
        & ~df["is_summary"].astype(str).str.casefold().isin(["true","1"])
    ].copy()

    x["part_count"]=x["location_string"].astype(str).map(
        lambda s: len([p for p in s.split(",") if p.strip()])
    )
    x=x[x["part_count"].le(4)].copy()

    grouped=(
        x.assign(location_string=x["location_string"].astype(str).str.strip().replace("", "(tom)"))
         .groupby(["location_string","title_location","type_original","part_count"],dropna=False)
         .size().reset_index(name="event_count")
         .sort_values(["event_count","part_count"],ascending=[False,True])
    )
    grouped.to_csv(OUT,index=False,encoding="utf-8")
    print(f"unknown_short_rows={len(x)} unique_short_locations={len(grouped)}")
    print(grouped.head(150).to_string(index=False))

if __name__=="__main__":
    main()
