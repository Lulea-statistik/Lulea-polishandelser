from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "summary_validation_sample.csv"

# Revised event definition:
# One event = one coherent event sequence/operation, normally separated by
# time and/or geography. Counts of persons, animals, vehicles, offences,
# fines or reports do NOT multiply the event count by themselves.
#
# Explicit counts of EVENTS (e.g. "three wildlife collisions") do count as
# three events. Aggregate counts of PERSONS (e.g. "five persons taken into
# custody under LOB") are not enough to determine the number of event
# sequences, so those rows are excluded from exact precision/recall QA.
AMBIGUOUS_PERSON_AGGREGATES = {
    "157101": "Två personer omhändertagna för fylleri anger två personer men inte om det var ett eller två händelseförlopp.",
    "169663": "Fyra LOB och en narkotikaprovtagning är personantal utan separerande tid/plats.",
    "288134": "Tre personer omhändertagna för fylleri saknar separation i tid/plats.",
    "313278": "Två personer i Luleå omhändertagna enligt LOB kan höra till ett eller två händelseförlopp.",
    "318538": "Fyra LOB samt sju LOB vid festivalen är personantal, inte säkra händelseantal.",
    "360595": "Fem LOB och övriga aggregerade anmälningar saknar tillräcklig separation för exakt händelseantal.",
    "428466": "Fem LOB anges som personantal utan separata tider/platser.",
    "460270": "Två personer omhändertagna för fylleri anges i en gemensam rapportperiod.",
    "468392": "Tre personer i Piteå omhändertagna enligt LOB saknar separation i tid/plats.",
    "77720": "Ett 10-tal LOB är ett ungefärligt personantal och kan inte översättas till exakt antal händelser.",
    "130429": "Sju personer omhändertagna för fylleri är personantal utan separata händelsemarkörer.",
    "199861": "Två personer omhändertagna enligt LOB saknar separat tid/plats.",
    "204674": "Två personer omhändertagna för fylleri saknar separat tid/plats.",
    "208254": "Fem LOB samt några ytterligare berusade personer är personantal/vagt antal, inte säkert händelseantal.",
    "223057": "Två personer omhändertagna för fylleri saknar separat tid/plats.",
    "233601": "Tre LOB och fyra narkotikaprovtagningar är personantal utan separata händelsemarkörer.",
    "234724": "En LOB och en narkotikaprovtagning kan vara separata eller del av samma händelseförlopp.",
    "250618": "Fyra personer omhändertagna enligt LOB saknar separat tid/plats.",
    "254751": "Ett LOB och en narkotikaprovtagning anges aggregerat utan separation i tid/plats.",
    "257831": "En narkotikamisstanke och två LOB anges aggregerat; personantalet bestämmer inte antal händelser.",
    "265796": "Två personer omhändertagna för fylleri saknar separat tid/plats.",
    "272984": "Ett LOB och en narkotikaprovtagning anges i gemensam rapportperiod utan separerande plats/tid.",
    "274610": "Fyra LOB är ett totalantal personer och kan dessutom inkludera den tidsatta LOB-händelsen 03:11.",
    "285442": "Fem personer omhändertagna enligt LOB saknar separata tider/platser.",
    "498304": "Två LOB i Piteå och en i Boden ger minst två geografiska händelseförlopp men inte exakt om Piteåfallen var ett eller två.",
}

# The two already known vague event-count rows remain non-exact.
AMBIGUOUS_EVENT_COUNTS = {
    "429": "Texten säger 'ett antal viltolyckor' utan exakt antal.",
    "8999": "Texten säger 'några trafikolyckor' utan exakt antal.",
}

def main() -> None:
    df = pd.read_csv(SAMPLE, dtype={"event_id":"string"}, low_memory=False)
    for col in ["event_definition_status", "event_definition_note"]:
        if col not in df.columns:
            df[col] = pd.NA

    # Exact rows retain the existing manual QA values.
    exact_mask = df["parser_correct_count"].notna()
    df.loc[exact_mask, "event_definition_status"] = "exact"

    all_amb = {**AMBIGUOUS_PERSON_AGGREGATES, **AMBIGUOUS_EVENT_COUNTS}
    for eid, note in all_amb.items():
        m = df["event_id"].astype(str).eq(eid)
        if not m.any():
            continue
        for col in [
            "manual_count","manual_lulea_count","parser_correct_count",
            "parser_false_positive_count","parser_missed_count"
        ]:
            df.loc[m, col] = pd.NA
        df.loc[m, "event_definition_status"] = "ambiguous"
        df.loc[m, "event_definition_note"] = note
        df.loc[m, "qa_note"] = "Ej exakt händelseräkningsbar enligt reviderad definition: " + note

    df.to_csv(SAMPLE, index=False, encoding="utf-8")
    print(f"exact_rows={(df['event_definition_status']=='exact').sum()}")
    print(f"ambiguous_rows={(df['event_definition_status']=='ambiguous').sum()}")

if __name__ == "__main__":
    main()
