from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
OUT = ROOT / "data" / "unknown_geography_candidates.csv"
SUMMARY = ROOT / "data" / "unknown_geography_candidate_summary.csv"

GENERIC = {
    "norrbotten", "norrbottens län", "norrbottens lan", "sverige",
    "norrbottens kommun", "norrbottens läns",
}
MUNICIPALITY_WORDS = {
    "arvidsjaur","arjeplog","boden","gällivare","haparanda","jokkmokk","kalix",
    "kiruna","luleå","pajala","piteå","älvsbyn","överkalix","övertorneå",
}


def norm(value: str) -> str:
    s = unicodedata.normalize("NFKD", str(value or "").casefold())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9åäö -]+", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -")


def candidate_parts(value: str) -> list[str]:
    out = []
    for raw in str(value or "").split(","):
        p = raw.strip()
        n = norm(p)
        if len(n) < 3 or len(n) > 45:
            continue
        if n in {norm(x) for x in GENERIC}:
            continue
        if any(norm(m) == n.replace(" kommun", "").strip() for m in MUNICIPALITY_WORDS):
            continue
        if re.fullmatch(r"\d{4}[a-z]{2}\d{3}", n):
            continue
        if re.fullmatch(r"\d+", n):
            continue
        out.append(p)
    return out


def main() -> None:
    df = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False).fillna("")
    known = df[
        df["municipality"].astype(str).str.strip().ne("")
        & ~df["is_summary"].astype(str).str.casefold().isin(["true","1"])
        & df["municipality_source"].astype(str).isin(["api","municipality_name","lulea_place_name"])
    ].copy()

    evidence = defaultdict(Counter)
    display = {}
    for _, r in known.iterrows():
        muni = str(r["municipality"]).strip()
        for part in candidate_parts(r.get("location_string","")):
            n = norm(part)
            evidence[n][muni] += 1
            display.setdefault(n, part)

    safe = {}
    for n, counts in evidence.items():
        total = sum(counts.values())
        muni, best = counts.most_common(1)[0]
        if total >= 5 and best == total:
            safe[n] = (muni, total)

    unknown = df[
        df["geography_group"].astype(str).eq("Norrbotten, okänd kommun")
        & ~df["is_summary"].astype(str).str.casefold().isin(["true","1"])
    ].copy()

    rows = []
    for _, r in unknown.iterrows():
        hits = {}
        for part in candidate_parts(r.get("location_string","")):
            n = norm(part)
            if n in safe:
                muni, count = safe[n]
                hits.setdefault(muni, []).append((part, count))
        if len(hits) != 1:
            continue
        muni = next(iter(hits))
        parts = hits[muni]
        rows.append({
            "event_id": r.get("event_id",""),
            "date": r.get("date",""),
            "type_original": r.get("type_original",""),
            "title_location": r.get("title_location",""),
            "location_string": r.get("location_string",""),
            "candidate_municipality": muni,
            "matched_places": " | ".join(sorted({p for p,_ in parts})),
            "min_training_count": min(c for _,c in parts),
            "max_training_count": max(c for _,c in parts),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=[
            "event_id","date","type_original","title_location","location_string",
            "candidate_municipality","matched_places","min_training_count","max_training_count"
        ])
    out.to_csv(OUT,index=False,encoding="utf-8")

    if len(out):
        summary = (
            out.groupby(["candidate_municipality","matched_places"], dropna=False)
            .size().reset_index(name="unknown_event_count")
            .sort_values(["unknown_event_count","candidate_municipality"], ascending=[False,True])
        )
    else:
        summary = pd.DataFrame(columns=["candidate_municipality","matched_places","unknown_event_count"])
    summary.to_csv(SUMMARY,index=False,encoding="utf-8")
    print(f"safe_empirical_place_names={len(safe)} unknown_candidate_events={len(out)}")
    if len(summary):
        print(summary.head(80).to_string(index=False))


if __name__ == "__main__":
    main()
