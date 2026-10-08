from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.csv"
DETAILS = ROOT / "data" / "summary_details.csv"
OUT = ROOT / "data" / "summary_validation_sample.csv"
OUT_COMPACT = ROOT / "data" / "summary_validation_compact.tsv"

SAMPLE_N = 200


def stable_rank(event_id: str) -> int:
    return int(hashlib.sha256(str(event_id).encode("utf-8")).hexdigest()[:16], 16)


def main() -> None:
    if not EVENTS.exists() or EVENTS.stat().st_size == 0:
        raise SystemExit("data/events.csv saknas eller är tom")
    if not DETAILS.exists() or DETAILS.stat().st_size == 0:
        raise SystemExit("data/summary_details.csv saknas eller är tom")

    events = pd.read_csv(EVENTS, dtype={"event_id": "string"}, low_memory=False)
    details = pd.read_csv(DETAILS, dtype={"parent_event_id": "string"}, low_memory=False)

    is_summary = events.get("is_summary", pd.Series(False, index=events.index)).astype(str).str.casefold().isin(["true", "1"])
    type_summary = events.get("type_original", pd.Series("", index=events.index)).fillna("").str.casefold().str.startswith("sammanfattning")
    summaries = events[is_summary | type_summary].copy()

    extracted = (
        details.groupby("parent_event_id")
        .size()
        .rename("extracted_count")
        .reset_index()
    )
    summaries = summaries.merge(extracted, how="left", left_on="event_id", right_on="parent_event_id")
    summaries["extracted_count"] = summaries["extracted_count"].fillna(0).astype(int)

    # Deterministiskt, reproducerbart urval, stratifierat över år så att både äldre
    # och nyare textformat finns med i kvalitetskontrollen.
    summaries["year_num"] = pd.to_numeric(summaries.get("year"), errors="coerce")
    summaries["rank"] = summaries["event_id"].map(stable_rank)

    years = [int(y) for y in sorted(summaries["year_num"].dropna().unique())]
    per_year = max(1, SAMPLE_N // max(1, len(years)))
    parts = []
    for year in years:
        part = summaries[summaries["year_num"] == year].sort_values("rank").head(per_year)
        parts.append(part)

    sample = pd.concat(parts, ignore_index=True) if parts else summaries.iloc[0:0].copy()
    if len(sample) < SAMPLE_N:
        already = set(sample["event_id"].astype(str))
        extra = summaries[~summaries["event_id"].astype(str).isin(already)].sort_values("rank").head(SAMPLE_N - len(sample))
        sample = pd.concat([sample, extra], ignore_index=True)
    sample = sample.head(SAMPLE_N).copy()

    cols = [
        "event_id","date","year","type_original","headline","description","content",
        "title_location","location_string","geography_group","external_source_link",
        "brottsplatskartan_url","extracted_count"
    ]
    for c in cols:
        if c not in sample.columns:
            sample[c] = ""

    # Fält för manuell validering fylls i senare.
    sample["manual_count"] = ""
    sample["manual_lulea_count"] = ""
    sample["parser_correct_count"] = ""
    sample["parser_false_positive_count"] = ""
    sample["parser_missed_count"] = ""
    sample["qa_note"] = ""

    out_cols = cols + [
        "manual_count","manual_lulea_count","parser_correct_count",
        "parser_false_positive_count","parser_missed_count","qa_note"
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ordered = sample[out_cols].sort_values(["year","date","event_id"]).copy()
    ordered.to_csv(OUT, index=False, encoding="utf-8")

    compact = ordered[["event_id","date","year","type_original","content","extracted_count"]].copy()
    compact["content"] = (
        compact["content"].fillna("").astype(str)
        .str.replace("\r", " ", regex=False)
        .str.replace("\n", " ", regex=False)
        .str.replace("\t", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.slice(0, 3200)
    )
    compact.to_csv(OUT_COMPACT, sep="\t", index=False, encoding="utf-8")

    print(
        f"validation_sample={len(sample)} "
        f"years={sample['year'].nunique()} "
        f"mean_extracted={sample['extracted_count'].mean():.3f}"
    )


if __name__ == "__main__":
    main()
