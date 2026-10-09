from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
OUT = ROOT / "data" / "unknown_geography_reason_summary.csv"
TITLES = ROOT / "data" / "unknown_geography_title_locations.csv"
TYPES = ROOT / "data" / "unknown_geography_type_summary.csv"

def main() -> None:
    df = pd.read_csv(EVENTS, dtype={"event_id":"string"}, low_memory=False).fillna("")
    x = df[df["geography_group"].astype(str).eq("Norrbotten, okänd kommun")].copy()
    x["is_summary_norm"] = x["is_summary"].astype(str).str.casefold().isin(["true","1"])
    x["reason"] = x["municipality_source"].astype(str).str.strip().replace("", "unknown")

    reason = (
        x.groupby(["reason","is_summary_norm"], dropna=False)
         .size().reset_index(name="event_count")
         .sort_values("event_count", ascending=False)
    )
    reason.to_csv(OUT,index=False,encoding="utf-8")

    titles = (
        x.assign(title_location=x["title_location"].astype(str).str.strip().replace("", "(tom)"))
         .groupby(["title_location","reason","is_summary_norm"], dropna=False)
         .size().reset_index(name="event_count")
         .sort_values("event_count", ascending=False)
    )
    titles.to_csv(TITLES,index=False,encoding="utf-8")

    types = (
        x.assign(type_original=x["type_original"].astype(str).str.strip().replace("", "(tom)"))
         .groupby(["type_original","reason","is_summary_norm"], dropna=False)
         .size().reset_index(name="event_count")
         .sort_values("event_count", ascending=False)
    )
    types.to_csv(TYPES,index=False,encoding="utf-8")

    print(f"unknown_norrbotten_rows={len(x)}")
    print("REASONS")
    print(reason.head(30).to_string(index=False))
    print("TOP TITLE_LOCATIONS")
    print(titles.head(50).to_string(index=False))
    print("TOP TYPES")
    print(types.head(40).to_string(index=False))

if __name__=="__main__":
    main()
