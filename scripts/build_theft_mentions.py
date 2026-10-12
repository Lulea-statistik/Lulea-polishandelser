"""Public theft-object mentions: candidates, not confirmed crime counts or offenders."""
from pathlib import Path
import re
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/events.csv"
OUT=ROOT/"data/theft_object_mentions.csv"
RULES={
 "Fyrhjuling / ATV":r"\b(?:fyrhjuling\w*|atv|terränghjuling\w*)\b",
 "Snöskoter":r"\b(?:snöskotr\w*|snöskoter\w*|skoter\w*)\b",
 "Bil":r"\b(?:personbil\w*|bilstöld\w*|bil\w*)\b",
 "Motorcykel / moped":r"\b(?:motorcykel\w*|mc|moped\w*)\b",
 "Cykel":r"\b(?:cykel\w*|elcykel\w*)\b",
 "Båt / båtmotor":r"\b(?:båt\w*|utombord\w*|båtmotor\w*)\b",
 "Verktyg / maskin":r"\b(?:verktyg\w*|arbetsmaskin\w*|motorsåg\w*)\b",
}
# Restrict candidates to explicit theft/burglary terms in the report text.
# Swedish conjugations: stöld/stölder; stjäla/stjäl/stal/stulen/stulit;
# tillgripa/tillgriper/tillgrep/tillgripit/tillgripen; inbrott.
# Prefix allows compounds such as bilstöld and cykelstöld.
THEFT=re.compile(
 r"(?i)(?<!\w)(?:\w*stöld\w*|\w*inbrott\w*|"
 r"stjäla|stjäl|stjäls|stjäles|stjälas|stjälande|"
 r"stal|stals|stulit|stulits|stulen|stulet|stulna|stulne|"
 r"tillgripa|tillgriper|tillgrips|tillgrep|tillgreps|"
 r"tillgripit|tillgripits|tillgripen|tillgripet|tillgripna|"
 r"tillgrepp\w*)(?!\w)"
)
NEGATE=re.compile(r"(?i)\b(?:förhindrat|försök att förhindra|ingen stöld|inte stulit|ej stulen|stöldgods återfunnet)\b")
def main():
 df=pd.read_csv(SRC,dtype={"event_id":"string"},low_memory=False).fillna("")
 df=df[df["geography_group"].astype(str).str.contains("kommun|Norrbotten",case=False,regex=True)]
 df=df[~df["is_summary"].astype(str).str.casefold().isin(("true","1"))]
 out=[]
 for row in df.itertuples(index=False):
  d=row._asdict()
  title=str(d.get("headline","")); typ=str(d.get("type_original",""))
  body=" ".join(str(d.get(k,"")) for k in ("headline","description","content"))
  if not THEFT.search(body): continue
  categories=[name for name,pat in RULES.items() if re.search(pat,body,re.I)]
  if not categories: categories=["Övrig / okänd"]
  date=pd.to_datetime(d.get("date"),errors="coerce")
  if pd.isna(date):continue
  for name in categories:
   out.append({"date":date.date().isoformat(),"year":date.year,"month":date.month,
    "week":date.strftime("%G-W%V"),"geography_group":d.get("geography_group",""),
    "object_category":name,"event_id":d.get("event_id",""),
    "headline":title,"theft_match":THEFT.search(body).group(0),"source_url":d.get("external_source_link") or d.get("brottsplatskartan_url") or ""})
 result=pd.DataFrame(out,columns=["date","year","month","week","geography_group","object_category","event_id","headline","theft_match","source_url"])
 result.drop_duplicates(["event_id","object_category"],inplace=True)
 OUT.parent.mkdir(exist_ok=True,parents=True)
 result.to_csv(OUT,index=False)
 print("candidate object mentions:",len(result),"unique reports:",result.event_id.nunique())
if __name__=="__main__": main()
