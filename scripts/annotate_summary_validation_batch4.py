from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

QA = {
    "9524": (0,0,0,0,0,"Hänvisar bara till redan publicerade notiser; inga nya underhändelser."),
    "50334": (0,0,0,0,0,"Endast lugn/inget att rapportera."),
    "51361": (4,1,4,0,0,"Fyra tidsatta händelser."),
    "52192": (0,0,0,0,0,"Ingen konkret underhändelse."),
    "55670": (0,0,0,0,0,"Ingen konkret underhändelse."),
    "57115": (6,2,6,0,0,"Sex konkreta tidsatta händelser."),
    "59744": (0,0,0,0,0,"Ingen konkret underhändelse."),
    "60074": (3,1,3,0,0,"Tre tidsatta händelser."),
    "60388": (0,0,0,0,0,"Ingen konkret underhändelse."),
    "62845": (2,1,2,0,0,"Två tidsatta händelser."),
    "64376": (0,0,0,0,0,"Tom sammanfattning."),
    "64592": (2,1,2,0,0,"Två tidsatta händelser."),
    "65791": (2,0,2,0,0,"Två konkreta händelser; senare text säger inga enskilda händelser."),
    "67486": (0,0,0,0,0,"Tom sammanfattning."),
    "68137": (3,1,3,1,0,"Tre faktiska händelser; 02:30 lugn-status är falsk träff."),
    "69059": (5,3,5,0,0,"Fem tidsatta händelser."),
    "72000": (3,1,3,0,0,"Tre tidsatta händelser."),
    "73986": (0,0,0,0,0,"Tom sammanfattning."),
    "77720": (13,0,3,0,10,"Cirka tio LOB + avvisning/knivlag + skadegörelse + rattfylleri; parsern fångar tre."),
    "82132": (3,0,3,0,0,"Tre tidsatta händelser utanför Norrbotten/Luleå."),
    "85027": (3,1,3,1,0,"Tre faktiska händelser; 00:00 är rapportperiod och falsk träff."),
    "90913": (2,0,2,0,0,"Två tidsatta händelser."),
    "91110": (3,1,3,0,0,"Tre tidsatta händelser."),
    "102708": (3,0,3,0,0,"Tre tidsatta händelser."),
    "110917": (0,0,0,0,0,"Inget att rapportera."),
    "112764": (2,0,2,0,0,"Två trafikbrott."),
    "130429": (13,1,4,0,9,"Sju LOB + en offentlig urinering + tre tidsatta händelser + två nykterhetskontroller som en sammanhållen kontrollpost + en viltolycka; konservativt 13."),
    "130657": (4,1,4,0,0,"Tre tidsatta händelser plus ett LOB-ingripande."),
    "134567": (3,2,3,1,0,"Tre faktiska händelser; extra otidsatt narkotikapost duplicerar 17:42-händelsen."),
    "135252": (0,0,0,0,0,"Tom sammanfattning."),
    "136409": (8,5,8,0,0,"Åtta konkreta tidsatta händelser; lugn-status ignoreras."),
    "141081": (7,1,1,0,6,"En tidsatt Luleå-rattfylla plus sex viltolyckor."),
    "143126": (3,0,0,0,3,"Tre explicit angivna viltolyckor."),
    "146282": (1,0,1,1,0,"En rattfyllerihändelse; 17:45 är allmän trafikinformation och falsk träff."),
    "153463": (0,0,0,0,0,"Inga händelser att rapportera."),
    "153948": (0,0,0,0,0,"Endast generell arbetsbelastning/kontroller."),
    "154132": (0,0,0,0,0,"Lugnt i länet, inget att rapportera."),
    "198433": (5,1,5,0,0,"Fem tidsatta händelser."),
    "199861": (5,0,3,0,2,"Två LOB plus tre tidsatta händelser."),
    "204291": (4,0,1,0,3,"Ett LOB, en misshandel och två viltolyckor."),
    "204674": (2,0,0,0,2,"Två explicit angivna LOB-ingripanden."),
    "208254": (8,0,4,0,4,"Fem LOB samt tre tidsatta händelser; externa redan publicerade trafikolyckor räknas inte på nytt."),
    "208869": (4,1,4,0,0,"Fyra konkreta händelser; inget-att-rapportera-rad ignoreras."),
    "210596": (3,0,2,0,1,"Ett LOB plus två tidsatta händelser."),
    "212569": (1,1,1,0,0,"En trafikbrottshändelse i Luleå.")
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
