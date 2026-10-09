from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data"/"summary_details_dedup.csv"
OUT=ROOT/"data"/"summary_unknown_place_audit.csv"

def main():
    df=pd.read_csv(SRC,dtype=str,low_memory=False).fillna("")
    x=df[df["geography_group"].astype(str).eq("Norrbotten, okänd kommun")].copy()
    x["place_text_norm"]=x["place_text"].astype(str).str.strip().replace("", "(tom)")
    out=(
        x.groupby(["place_text_norm","event_type_extracted"],dropna=False)
         .size().reset_index(name="event_count")
         .sort_values("event_count",ascending=False)
    )
    out.to_csv(OUT,index=False,encoding="utf-8")
    print(f"summary_unknown_rows={len(x)} unique_place_texts={len(out)}")
    print(out.head(150).to_string(index=False))

if __name__=="__main__":
    main()
