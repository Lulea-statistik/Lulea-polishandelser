from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/"data/events.csv"
dst=ROOT/"data/review_borje_full_text.csv"
summary=ROOT/"data/review_borje_patterns.csv"
df=pd.read_csv(src,dtype=str,keep_default_na=False,low_memory=False)
location=df["location_string"].str.contains(r"(?i)börje",regex=True,na=False)
headline=df["headline"].str.contains(r"(?i)börje",regex=True,na=False)
description=df["description"].str.contains(r"(?i)börje",regex=True,na=False)
content=df["content"].str.contains(r"(?i)börje",regex=True,na=False)
subset=df[location|headline|description|content].copy()
cols=["event_id","date","type_original","title_location","location_string",
      "municipality","municipality_source","geography_group","is_summary",
      "headline","description","content","external_source_link","brottsplatskartan_url"]
subset[cols].to_csv(dst,index=False,encoding="utf-8")
(
 subset.groupby(["geography_group","type_original","location_string"],dropna=False)
 .size().reset_index(name="count").sort_values("count",ascending=False)
 .to_csv(summary,index=False,encoding="utf-8")
)
print("Börje full text records",len(subset))
print("Location matches",int(location.sum()),"headline",int(headline.sum()),
      "description",int(description.sum()),"content",int(content.sum()))
