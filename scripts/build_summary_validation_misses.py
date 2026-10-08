from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/"data"/"summary_validation_sample.csv"
out=ROOT/"data"/"summary_validation_misses.tsv"
df=pd.read_csv(src,dtype={"event_id":"string"},low_memory=False)
miss=pd.to_numeric(df.get("parser_missed_count"),errors="coerce")
status=df.get("event_definition_status",pd.Series("",index=df.index)).fillna("")
m=df[(status=="exact") & (miss>0)].copy()
cols=["event_id","date","content","extracted_count","parser_lulea_count","manual_count","manual_lulea_count","parser_correct_count","parser_false_positive_count","parser_missed_count","qa_note"]
m[cols].to_csv(out,sep="\t",index=False,encoding="utf-8")
print(f"miss_rows={len(m)} missed_events={int(m['parser_missed_count'].sum())}")
