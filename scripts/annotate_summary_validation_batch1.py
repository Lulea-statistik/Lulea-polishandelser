from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

# Första manuella QA-blocket. Endast rader där antal faktiska underhändelser
# kan bestämmas tydligt från texten annoteras. Vaga mängdangivelser som
# "ett antal" lämnas avsiktligt orörda.
QA = {
    "178":   (0, 0, 0, 0, 0, "Ingen konkret underhändelse."),
    "715":   (2, 0, 2, 0, 0, "Två tidsatta händelser; singelolycka + fordonsstopp."),
    "1156":  (0, 0, 0, 0, 0, "Ingen händelse att rapportera."),
    "1710":  (0, 0, 0, 0, 0, "Inga akuta händelser."),
    "2795":  (3, 1, 3, 0, 0, "Tre separata tidsatta händelser, varav en Luleå."),
    "3347":  (1, 0, 1, 0, 0, "En trafikolycka i Piteå."),
    "3701":  (0, 0, 0, 0, 0, "Allmän beskrivning av arbete, inga diskreta händelser."),
    "3899":  (2, 0, 2, 0, 0, "Två konkreta händelser; 02:00 är statusrad."),
    "6572":  (11, 4, 11, 0, 0, "Elva tidsatta incidenter; 3 renar avser en och samma olycka."),
    "6581":  (0, 0, 0, 0, 0, "Inget att rapportera."),
    "8164":  (0, 0, 0, 0, 0, "Rapportperiod utan händelser."),
    "8234":  (0, 0, 0, 0, 0, "Inga akuta händelser."),
    "8346":  (1, 0, 1, 0, 0, "En viltolycka."),
    "8848":  (0, 0, 0, 0, 0, "Brottsförebyggande kontroller utan diskreta rapporterade incidenter."),
    "9601":  (2, 0, 2, 0, 0, "Två tidsatta Kalix-händelser."),
    "23682": (1, 0, 1, 0, 0, "En hastighetskontroll; fyra böter är inte fyra händelser."),
    "23861": (5, 1, 5, 0, 0, "Fem tidsatta händelser, varav en i Luleå."),
    "25926": (4, 1, 4, 0, 0, "Fyra tidsatta händelser, varav en i Luleå."),
    "28264": (1, 0, 1, 0, 0, "En konkret tidsatt händelse; övrig text är generell sammanfattning."),
    "31613": (6, 1, 6, 0, 0, "Sex tidsatta händelser, varav en i Luleå."),
    "32993": (0, 0, 0, 0, 0, "Ingen konkret underhändelse."),
    "33271": (0, 0, 0, 0, 0, "Endast generell beskrivning."),
    "34037": (1, 0, 1, 0, 0, "En konkret händelse."),
    "34873": (0, 0, 0, 0, 0, "Ingen konkret underhändelse."),
    "35138": (1, 0, 1, 0, 0, "En trafikolycka."),
    "36958": (0, 0, 0, 0, 0, "Brottsförebyggande arbete, inga diskreta incidenter."),
    "37121": (1, 0, 1, 0, 0, "En ringa stöld."),
    "38084": (1, 0, 1, 0, 0, "En refererad misshandel i Kiruna."),
    "43377": (3, 1, 3, 0, 0, "Tre tidsatta händelser, varav en i Luleå."),
    "43692": (9, 2, 9, 0, 0, "Nio tidsatta händelser, varav två i Luleå."),
    "46014": (0, 0, 0, 0, 0, "Inget att rapportera."),
}

def main() -> None:
    df = pd.read_csv(SAMPLE, dtype={"event_id":"string"}, low_memory=False)
    for eid, vals in QA.items():
        mask = df["event_id"].astype(str).eq(eid)
        if not mask.any():
            continue
        manual, lulea, correct, fp, missed, note = vals
        df.loc[mask, "manual_count"] = manual
        df.loc[mask, "manual_lulea_count"] = lulea
        df.loc[mask, "parser_correct_count"] = correct
        df.loc[mask, "parser_false_positive_count"] = fp
        df.loc[mask, "parser_missed_count"] = missed
        df.loc[mask, "qa_note"] = note
    df.to_csv(SAMPLE, index=False, encoding="utf-8")
    print(f"annotated_rows={df['parser_correct_count'].notna().sum()}")

if __name__ == "__main__":
    main()
