from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

QA = {
    "317620": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
    "317677": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
    "317751": (1, 1, 1, 0, 0, "En stöldhändelse i Luleå."),
    "318538": (15, 0, 4, 0, 11, "Fyra tidsatta händelser + fyra LOB + sju LOB under festivalen; övriga festivalåtgärder räknas inte som separata incidenter."),
    "347208": (8, 2, 8, 0, 0, "Åtta tidsatta händelser."),
    "353441": (3, 0, 3, 0, 0, "Två tidsatta händelser samt en viltolycka."),
    "360595": (9, 0, 3, 0, 6, "Fem LOB, minst två övriga anmälda brottskategorier samt två tidsatta händelser; konservativt räknat nio incidenter."),
    "412023": (1, 0, 1, 0, 0, "En konkret älgolycka."),
    "428466": (10, 2, 4, 0, 6, "Fem LOB + två separata misshandelsärenden i Luleå + tre tidsatta Boden-händelser."),
    "431380": (4, 1, 4, 0, 0, "Fyra tidsatta händelser."),
    "447624": (1, 0, 1, 0, 0, "En tidsatt händelse."),
    "450758": (5, 1, 5, 0, 0, "Fem tidsatta händelser; typklassning påverkar inte händelseräkningen."),
    "453042": (3, 0, 3, 0, 0, "Tre tidsatta händelser."),
    "460270": (4, 0, 3, 0, 1, "Två LOB + misshandel + trafikkontroll; 00:00 sammanfattar två LOB som en parserpost."),
    "468392": (7, 0, 3, 0, 4, "Tre LOB i Piteå, två tidsatta händelser och två viltolyckor."),
    "470799": (1, 0, 1, 0, 0, "En viltolycka."),
    "497556": (3, 1, 3, 0, 0, "Tre tidsatta händelser."),
    "498392": (6, 1, 2, 0, 4, "Två LOB Piteå + en LOB Boden + ett narkotikaärende Luleå + två tidsatta händelser."),
    "498388": (2, 0, 2, 0, 0, "Inbrott och viltolycka."),
    "501953": (1, 0, 1, 0, 0, "En tidsatt händelse."),
    "502035": (6, 0, 3, 0, 3, "Tre tidsatta händelser samt tre viltolyckor."),
    "502094": (1, 1, 1, 0, 0, "En viltolycka i Luleå."),
    "504029": (4, 1, 4, 0, 0, "Fyra tidsatta händelser."),
    "504309": (3, 2, 3, 0, 0, "Tre tidsatta händelser."),
    "504360": (0, 0, 0, 0, 0, "Tom sammanfattning."),
    "504811": (3, 1, 3, 0, 0, "Tre tidsatta händelser."),
    "505703": (2, 0, 1, 0, 1, "En tidsatt narkotikahändelse plus ett LOB-ingripande."),
    "506148": (2, 0, 2, 0, 0, "Två viltolyckor."),
    "507374": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
    "508203": (1, 0, 0, 0, 1, "Ett ej tidsatt LOB-ingripande."),
    "509097": (0, 0, 0, 0, 0, "Tom sammanfattning."),
    "510972": (0, 0, 0, 0, 0, "Tom sammanfattning."),
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
