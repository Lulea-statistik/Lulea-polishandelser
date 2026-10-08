from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
DETAILS = ROOT / "data" / "summary_details.csv"
OUT = ROOT / "data" / "summary_details_dedup.csv"
OUT_MONTHLY = ROOT / "data" / "summary_details_extra_monthly.csv"

TYPE_RULES = [
    (r"viltolycka|renolycka|rådjursolycka|älgolycka|trafikolycka.*vilt|singelolycka|kollider\w* med (?:älg|ren|rådjur|hjort)", "Trafikolycka"),
    (r"drograttfylleri|rattfylleri", "Rattfylleri"),
    (r"olovlig körning", "Olovlig körning"),
    (r"trafikkontroll|hastighetskontroll|nykterhetskontroll", "Trafikkontroll"),
    (r"trafikbrott|vårdslöshet i trafik", "Trafikbrott"),
    (r"trafikolycka|kollision|krock", "Trafikolycka"),
    (r"arbetsplatsolycka|fallolycka", "Arbetsplatsolycka"),
    (r"misshand", "Misshandel"),
    (r"narkotik", "Narkotikabrott"),
    (r"stöld/inbrott|stöld genom inbrott|inbrott", "Inbrott"),
    (r"ringa stöld|snatt", "Stöld"),
    (r"stöld|stul|tillgrip", "Stöld"),
    (r"skadegör", "Skadegörelse"),
    (r"fylleri|\blob\b|tillnyktring", "Fylleri/LOB"),
    (r"olaga hot", "Olaga hot"),
    (r"ofred|förargelseväckande", "Ofredande/förargelse"),
    (r"brand", "Brand"),
    (r"rån", "Rån"),
    (r"fjällräddning", "Fjällräddning"),
    (r"sexualbrott|våldtäkt|sexuellt ofred", "Sexualbrott"),
    (r"mord|dråp", "Mord/dråp"),
]

WORD_RE = re.compile(r"[a-zåäö0-9]{4,}", re.I)
STOP = {
    "polisen","polis","patrull","platsen","personen","mannen","kvinnan","under",
    "efter","sedan","samt","också","detta","denna","någon","några","med",
    "för","och","att","som","har","hade","blir","blev","till","från"
}


def norm_type(value: str) -> str:
    text = (value or "").casefold()
    for pat, label in TYPE_RULES:
        if re.search(pat, text, re.I):
            return label
    return (value or "").strip()


def tokens(value: str) -> set[str]:
    return {w.casefold() for w in WORD_RE.findall(value or "") if w.casefold() not in STOP}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    jac = len(ta & tb) / max(1, len(ta | tb))
    seq = SequenceMatcher(None, (a or "")[:700].casefold(), (b or "")[:700].casefold()).ratio()
    return max(jac, seq * 0.75)


def main() -> None:
    events = pd.read_csv(EVENTS, dtype={"event_id":"string"}, low_memory=False)
    details = pd.read_csv(DETAILS, dtype={"parent_event_id":"string"}, low_memory=False)

    non = events[~events.get("is_summary", False).astype(str).str.casefold().isin(["true","1"])].copy()
    non["event_date"] = pd.to_datetime(non["date"], errors="coerce")
    non["norm_type"] = non.apply(
        lambda r: norm_type(" ".join(str(r.get(c,"") or "") for c in ["type_original","headline","description","content"])),
        axis=1,
    )
    non["match_text"] = non.apply(
        lambda r: " ".join(str(r.get(c,"") or "") for c in ["headline","description","content","location_string","title_location"]),
        axis=1,
    )

    details["event_date"] = pd.to_datetime(details["date"], errors="coerce")
    details["norm_type"] = details["event_type_extracted"].map(norm_type)
    details["duplicate_of_event_id"] = ""
    details["duplicate_score"] = 0.0
    details["duplicate_reason"] = ""

    # Conservative matching: same/adjacent publication date, compatible type,
    # plus municipality or strong textual overlap. We prefer false negatives
    # to incorrectly removing genuine hidden events.
    for idx, row in details.iterrows():
        dt = row["event_date"]
        if pd.isna(dt):
            continue
        lo, hi = dt - pd.Timedelta(days=1), dt + pd.Timedelta(days=1)
        cand = non[(non["event_date"] >= lo) & (non["event_date"] <= hi)]
        if row["norm_type"]:
            cand = cand[cand["norm_type"] == row["norm_type"]]
        if cand.empty:
            continue

        best = None
        best_score = 0.0
        best_reason = ""
        stext = " ".join(str(row.get(c,"") or "") for c in ["description","place_text","municipality"])
        smuni = str(row.get("municipality","") or "").strip()

        for _, c in cand.iterrows():
            cmuni = str(c.get("municipality","") or "").strip()
            muni_match = bool(smuni and cmuni and smuni.casefold() == cmuni.casefold())
            sim = similarity(stext, str(c.get("match_text","") or ""))
            same_day = c["event_date"] == dt

            score = sim + (0.18 if muni_match else 0) + (0.08 if same_day else 0)
            # Very strict threshold unless municipality agrees.
            is_dup = (muni_match and sim >= 0.20 and score >= 0.42) or sim >= 0.52
            if is_dup and score > best_score:
                best = c
                best_score = score
                best_reason = f"type+text{'+' + 'municipality' if muni_match else ''}{'+same_date' if same_day else ''}"

        if best is not None:
            details.at[idx,"duplicate_of_event_id"] = str(best.get("event_id",""))
            details.at[idx,"duplicate_score"] = round(float(best_score),3)
            details.at[idx,"duplicate_reason"] = best_reason

    details["include_as_extra"] = details["duplicate_of_event_id"].eq("")
    details.drop(columns=["event_date"], inplace=True)
    details.to_csv(OUT, index=False, encoding="utf-8")

    extra = details[details["include_as_extra"]].copy()
    if extra.empty:
        monthly = pd.DataFrame(columns=["year","month","geography_group","event_type_extracted","event_count"])
    else:
        monthly = (
            extra.groupby(["year","month","geography_group","event_type_extracted"], dropna=False)
            .size().reset_index(name="event_count")
            .sort_values(["year","month","geography_group","event_count"], ascending=[True,True,True,False])
        )
    monthly.to_csv(OUT_MONTHLY, index=False, encoding="utf-8")

    print(
        f"summary_details={len(details)} probable_duplicates={(~details['include_as_extra']).sum()} "
        f"extra_unique={details['include_as_extra'].sum()} "
        f"lulea_extra={((details['include_as_extra']) & (details['municipality']=='Luleå')).sum()}"
    )


if __name__ == "__main__":
    main()
