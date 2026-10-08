from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

QA = {
    "114031": (4,2,4,0,0,"LOB + viltolycka + två Luleå-händelser; parsern har fyra träffar."),
    "115303": (6,4,6,0,0,"Sex tidsatta händelser."),
    "120244": (2,2,2,0,0,"Två Luleå-händelser."),
    "120872": (3,1,3,0,0,"Tre tidsatta händelser; Rutvik räknas som Luleå."),
    "123526": (0,0,0,0,0,"Tom sammanfattning."),
    "125340": (7,2,7,0,0,"En viltolycka plus sex tidsatta händelser."),
    "126326": (1,1,1,0,0,"En grov brottshändelse i Luleå."),
    "130198": (1,0,1,0,0,"En sammanhållen trafikkontroll."),
    "213090": (4,1,3,0,1,"Två separata fortkörningar under 00:11-blocket, skadegörelse Luleå och trafikkontroll Boden."),
    "216141": (0,0,0,0,0,"Inga ärenden att rapportera."),
    "217849": (7,2,4,0,3,"Fyra tidsatta händelser plus tre viltolyckor, varav en i Luleå."),
    "218309": (6,0,3,0,3,"Tre tidsatta händelser plus tre renpåkörningar."),
    "218587": (8,2,7,0,1,"Ett ej tidsatt narkotikaärende plus sju tidsatta händelser."),
    "223057": (5,1,3,0,2,"Två LOB plus tre tidsatta händelser."),
    "224228": (0,0,0,0,0,"Inget att rapportera."),
    "230821": (1,1,1,0,0,"En Luleå-händelse."),
    "231662": (2,0,2,0,0,"Två tidsatta händelser."),
    "232771": (5,1,4,0,1,"Ett ej tidsatt LOB plus fyra tidsatta händelser."),
    "233601": (11,1,5,0,6,"Tre LOB + fyra narkotikaprovtagningar + fyra nya tidsatta händelser; tidigare länkad misshandel räknas inte på nytt.")
}

def main():
    df=pd.read_csv(SAMPLE,dtype={"event_id":"string"},low_memory=False)
    for eid,vals in QA.items():
        m=df["event_id"].astype(str).eq(eid)
        if not m.any(): continue
        manual,lulea,correct,fp,missed,note=vals
        df.loc[m,"manual_count"]=manual
        df.loc[m,"manual_lulea_count"]=lulea
        df.loc[m,"parser_correct_count"]=correct
        df.loc[m,"parser_false_positive_count"]=fp
        df.loc[m,"parser_missed_count"]=missed
        df.loc[m,"qa_note"]=note
    df.to_csv(SAMPLE,index=False,encoding="utf-8")
    print(f"annotated_rows={df['parser_correct_count'].notna().sum()}")

if __name__=="__main__":
    main()
