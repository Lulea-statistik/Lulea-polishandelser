from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
DETAILS = ROOT / "data" / "summary_details_dedup.csv"
OUT = ROOT / "data" / "unresolved_summaries.csv"
OUT_STATS = ROOT / "data" / "unresolved_summaries_stats.csv"

TIME_RE = re.compile(r"\b[0-2]?\d[:.]\d{2}\b")
MUNICIPALITY_WORDS = re.compile(
    r"(?i)\b(arvidsjaur|arjeplog|boden|gällivare|haparanda|jokkmokk|kalix|kiruna|luleå|pajala|piteå|älvsbyn|överkalix|övertorneå)\b"
)
EVENT_WORDS = re.compile(
    r"(?i)\b(misshandel|rattfylleri|narkotika|stöld|inbrott|skadegörelse|"
    r"trafikolycka|viltolycka|trafikkontroll|trafikbrott|brand|rån|olaga hot|"
    r"fylleri|omhändertagits|gripits|anhållits|provtagning)\b"
)


def truthy(series: pd.Series) -> pd.Series:
    return series.astype(str).str.casefold().isin(["true", "1"])


def text_of(row: pd.Series) -> str:
    for col in ("content", "description", "headline"):
        value = str(row.get(col, "") or "").strip()
        if value:
            return value
    return ""


def main() -> None:
    events = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    details = pd.read_csv(DETAILS, dtype={"parent_event_id": "string"}, low_memory=False)

    is_summary = truthy(events.get("is_summary", pd.Series(False, index=events.index)))
    parsed_ids = set(details["parent_event_id"].dropna().astype("string"))
    unresolved = events[is_summary & ~events["event_id"].astype("string").isin(parsed_ids)].copy()

    rows = []
    for _, r in unresolved.iterrows():
        text = text_of(r)
        rows.append({
            "event_id": r.get("event_id", ""),
            "date": r.get("date", ""),
            "year": r.get("year", ""),
            "type_original": r.get("type_original", ""),
            "geography_group": r.get("geography_group", ""),
            "municipality": r.get("municipality", ""),
            "has_time": bool(TIME_RE.search(text)),
            "has_municipality_name": bool(MUNICIPALITY_WORDS.search(text)),
            "has_event_word": bool(EVENT_WORDS.search(text)),
            "text_length": len(text),
            "headline": r.get("headline", ""),
            "content": text,
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, encoding="utf-8")

    if out.empty:
        stats = pd.DataFrame(columns=["reason_group", "count"])
    else:
        def group_reason(r):
            if r["has_time"] and r["has_event_word"]:
                return "tid + händelseord"
            if r["has_event_word"] and r["has_municipality_name"]:
                return "händelseord + kommun"
            if r["has_event_word"]:
                return "händelseord utan tydlig tid/kommun"
            if r["has_time"]:
                return "tid utan igenkänt händelseord"
            return "ingen tydlig struktur"

        out["reason_group"] = out.apply(group_reason, axis=1)
        stats = (
            out.groupby("reason_group", dropna=False)
            .size().reset_index(name="count")
            .sort_values("count", ascending=False)
        )
    stats.to_csv(OUT_STATS, index=False, encoding="utf-8")
    print(f"unresolved_summaries={len(out)}")
    if not stats.empty:
        print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
