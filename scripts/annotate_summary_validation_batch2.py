from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

# Andra QA-blocket: medvetet svårare fall med icke tidsatta mängduppgifter,
# statusrader och blandade format. Här räknas uttryckligen kvantifierade
# separata incidenter (t.ex. "två personer har omhändertagits") som två
# underhändelser när texten tydligt anger två separata ingripanden.
QA = {
    "156100": (3, 2, 3, 1, 0, "00:00 är rapportperiod/status och falsk träff; tre faktiska händelser."),
    "156608": (2, 0, 2, 1, 0, "00:33 lugn-status är falsk träff; två faktiska händelser."),
    "157101": (3, 0, 1, 0, 2, "Två ej tidsatta LOB/fylleri-ingripanden plus en tidsatt rattfyllerihändelse."),
    "157182": (3, 1, 2, 0, 1, "Två tidsatta händelser plus en ej tidsatt viltolycka."),
    "163986": (2, 0, 2, 0, 0, "Två konkreta tidsatta händelser; lugn-status ignoreras."),
    "164115": (4, 2, 4, 0, 0, "Fyra konkreta händelser; lugn-statusrader ignoreras."),
    "169663": (8, 1, 2, 0, 6, "Fyra LOB, ett narkotikaärende, två tidsatta händelser och en viltolycka."),
    "170877": (2, 0, 2, 0, 0, "Två konkreta händelser."),
    "170956": (4, 1, 4, 0, 0, "Fyra konkreta tidsatta händelser."),
    "174531": (2, 0, 1, 0, 1, "Ett narkotikaärende samt en viltolycka; parsern fångar bara viltolyckan."),
    "178475": (7, 2, 7, 0, 0, "En LOB/narkotika/tillgreppshändelse plus sex tidsatta händelser."),
    "180269": (4, 0, 4, 0, 0, "Tre tidsatta händelser samt en ej tidsatt viltolycka."),
    "180501": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
    "181192": (7, 2, 4, 0, 3, "Fyra tidsatta händelser plus tre uttryckligen angivna viltolyckor."),
    "184797": (3, 0, 0, 1, 3, "00:00 är rapportperiod; tre viltolyckor anges explicit och missas."),
    "190002": (4, 0, 1, 0, 3, "Ett trafikbrott samt tre explicit angivna viltolyckor."),
    "192428": (3, 1, 3, 0, 0, "Tre tidsatta händelser."),
    "193036": (1, 1, 1, 0, 0, "En narkotikahändelse i Luleå."),
    "195697": (3, 1, 3, 1, 0, "22:21 trafikbrott, 05:11 Luleå-kontroll, 06:07 samlad kontroll; 03:31 lugn-status är falsk."),
    "287501": (0, 0, 0, 0, 0, "Endast kontroller utan brottsmisstanke."),
    "288134": (7, 0, 4, 0, 3, "Fyra tidsatta händelser plus tre övriga LOB/fylleri-ingripanden."),
    "290630": (10, 1, 7, 0, 3, "Sju tidsatta händelser samt tre övriga konkreta ingripanden."),
    "291029": (4, 0, 1, 0, 3, "Två böteshändelser och tre separata trafikkontroller; parsern grupperar för mycket."),
    "292806": (3, 2, 3, 0, 0, "Tre konkreta händelser."),
    "292869": (5, 2, 2, 0, 3, "Två tidsatta Luleå-händelser samt två renpåkörningar och en viltolycka."),
    "294110": (1, 0, 1, 0, 0, "En trafikkontroll; två böter hör till samma kontroll."),
    "294247": (3, 0, 2, 0, 1, "Två tidsatta händelser plus ett ej tidsatt LOB-ingripande."),
    "294491": (3, 0, 2, 0, 1, "Ett LOB-ingripande, fordonsstöld och en viltolycka."),
    "295284": (2, 1, 2, 0, 0, "Arbetsplatsolycka i Luleå samt viltolycka i Gällivare."),
    "295484": (1, 0, 1, 0, 0, "En konkret ordningsbots-/förargelsehändelse."),
    "298265": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
    "299354": (3, 2, 3, 0, 0, "Tre tidsatta händelser."),
    "300669": (0, 0, 0, 0, 0, "Endast kontroller utan brottsmisstanke."),
    "300745": (2, 0, 2, 0, 0, "Två tidsatta händelser."),
    "300991": (2, 0, 1, 0, 1, "En tidsatt viltolycka plus ett ej tidsatt LOB-ingripande."),
    "305947": (4, 0, 3, 0, 1, "Tre tidsatta händelser plus ett ej tidsatt LOB-ingripande."),
    "307684": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
    "313278": (2, 2, 1, 0, 1, "Två LOB-ingripanden i Luleå; parsern fångar bara narkotikadelen som en post."),
    "314558": (4, 0, 4, 0, 0, "Fyra tidsatta händelser."),
    "317620": (2, 1, 2, 0, 0, "Två tidsatta händelser."),
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
