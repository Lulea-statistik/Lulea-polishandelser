from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

QA = {
    "234724": (4,0,3,0,1,"Ett LOB + ett narkotikaärende + två tidsatta händelser."),
    "236243": (0,0,0,0,0,"Endast kontroller utan brottsmisstanke."),
    "239285": (3,2,3,0,0,"Tre tidsatta händelser, två i Luleå."),
    "239961": (0,0,0,0,0,"Inget att rapportera."),
    "241645": (0,0,0,1,0,"Beach Party-status är ingen diskret händelse; parserns enda träff är falsk."),
    "243788": (1,0,1,0,0,"En trafikkontroll."),
    "245157": (3,1,3,0,0,"Inbrott Luleå, återfunnen person Piteå och viltolycka Pajala."),
    "245281": (3,1,2,0,1,"Rattfylleri, olaga hot Luleå och ett ej tidsatt LOB."),
    "245331": (4,1,4,0,0,"Fyra konkreta tidsatta händelser; lugn-rader ignoreras."),
    "248758": (1,0,1,0,0,"En singelolycka."),
    "250618": (7,0,3,0,4,"Fyra LOB plus tre tidsatta händelser."),
    "250784": (1,0,1,0,0,"En brand."),
    "254751": (5,0,3,0,2,"Tre tidsatta händelser plus ett LOB och ett narkotikaprovtagningstillfälle."),
    "256355": (1,0,0,0,1,"En misshandelshändelse utan klockslag."),
    "257831": (5,0,2,0,3,"Ett narkotikaärende + två LOB + två tidsatta händelser."),
    "258395": (1,0,1,0,0,"En renolycka; två renar i samma olycka."),
    "262850": (2,0,1,0,1,"Tillgrepp/smitningshändelsen är ett sammanhängande ärende plus ett LOB."),
    "263949": (4,0,2,0,2,"Två tidsatta händelser plus två viltolyckor."),
    "265463": (0,0,0,0,0,"Tom sammanfattning."),
    "265553": (4,0,2,1,2,"Tre separata skadegörelser i Haparanda + en trafikkontroll; 00:00-status är falsk parserträff."),
    "265796": (4,2,2,0,2,"Två Luleå-misshandelshändelser plus två LOB."),
    "265912": (4,1,4,0,0,"Fyra konkreta händelser, varav en viltolycka i Luleå."),
    "269269": (2,1,2,0,0,"Fjällräddning Kiruna och trafikkontroll Luleå."),
    "272321": (1,0,0,0,1,"Ett ej tidsatt LOB."),
    "272984": (3,0,2,0,1,"LOB + narkotikaprovtagning + trafikkontroll."),
    "274610": (8,2,4,0,4,"Fyra LOB plus fyra uppräknade ärenden; Luleå två."),
    "275966": (3,2,3,0,0,"Tre tidsatta händelser."),
    "275853": (4,0,1,0,3,"En trafikolycka plus tre viltolyckor."),
    "276237": (5,0,3,0,2,"Tre tidsatta händelser plus två viltolyckor."),
    "279128": (4,1,4,0,0,"Fyra tidsatta händelser."),
    "284842": (0,0,0,0,0,"Inga händelser att rapportera."),
    "285442": (8,0,3,0,5,"Fem LOB plus tre tidsatta händelser."),
    "498304": (6,1,2,0,4,"Tre LOB, ett narkotikaärende i Luleå och två tidsatta händelser.")
}

AMBIG = {
    "429": "Obestämbart exakt antal: texten säger 'ett antal viltolyckor'. Exkluderas från exakta precision/recall-tal.",
    "8999": "Obestämbart exakt antal: texten säger 'några trafikolyckor'. Exkluderas från exakta precision/recall-tal."
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
    for eid,note in AMBIG.items():
        m=df["event_id"].astype(str).eq(eid)
        if m.any():
            df.loc[m,"qa_note"]=note
    df.to_csv(SAMPLE,index=False,encoding="utf-8")
    print(f"annotated_rows={df['parser_correct_count'].notna().sum()}")
    print(f"ambiguous_rows={df['event_id'].astype(str).isin(AMBIG).sum()}")

if __name__=="__main__":
    main()
