from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/"data"/"summary_validation_sample.csv"
out=ROOT/"data"/"summary_validation_misses.tsv"
df=pd.read_csv(src,dtype={"event_id":"string"},low_memory=False)

for col in ["extracted_count","parser_correct_count","parser_false_positive_count","parser_missed_count"]:
    df[col]=pd.to_numeric(df.get(col),errors="coerce")

status=df.get("event_definition_status",pd.Series("",index=df.index)).fillna("")
exact=df[status=="exact"].copy()

old_parser=exact["parser_correct_count"]+exact["parser_false_positive_count"]
delta=exact["extracted_count"]-old_parser
add=delta.clip(lower=0)
recovered=pd.concat([add,exact["parser_missed_count"]],axis=1).min(axis=1)
removed=(-delta).clip(lower=0)
removed_fp=pd.concat([removed,exact["parser_false_positive_count"]],axis=1).min(axis=1)
removed_correct=(removed-removed_fp).clip(lower=0)

exact["current_correct_count"]=exact["parser_correct_count"]+recovered-removed_correct
exact["current_false_positive_count"]=exact["parser_false_positive_count"]+(add-recovered).clip(lower=0)-removed_fp
exact["current_missed_count"]=exact["parser_missed_count"]-recovered+removed_correct

m=exact[exact["current_missed_count"]>0].copy()
cols=["event_id","date","content","extracted_count","parser_lulea_count","manual_count","manual_lulea_count","current_correct_count","current_false_positive_count","current_missed_count","qa_note"]
m[cols].to_csv(out,sep="\t",index=False,encoding="utf-8")
print(f"miss_rows={len(m)} missed_events={int(m['current_missed_count'].sum())}")
