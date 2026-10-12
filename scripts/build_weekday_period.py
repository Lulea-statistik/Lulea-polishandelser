"""Daily observation coverage and weekday/time-block aggregates.

An unknown time is never assigned from the publication timestamp.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ("Eftermiddag", "Kväll", "Kväll/natt", "Natt")
OUT = ROOT / "data" / "weekday_period_observations.csv"

def valid_dates(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.loc[df["date"].notna()].copy()

def block_from_time(value):
    text = str(value or "").strip().replace(".", ":")
    if ":" not in text:
        return ""
    try:
        h, minute = (int(v) for v in text.split(":", 1))
    except ValueError:
        return ""
    if h > 23 or minute > 59:
        return ""
    if 12 <= h < 18:
        return "Eftermiddag"
    if 18 <= h < 22:
        return "Kväll"
    if h >= 22 or h < 6:
        return "Natt"
    return ""

def main():
    events = pd.read_csv(ROOT / "data" / "events.csv", low_memory=False, dtype={"event_id": "string"})
    details = pd.read_csv(ROOT / "data" / "summary_details_dedup.csv", low_memory=False, dtype={"parent_event_id": "string"})
    stats = pd.read_csv(ROOT / "data" / "excluded_administrative_notices.csv", low_memory=False, dtype={"event_id": "string"})
    is_summary = events["is_summary"].astype(str).str.lower().isin(("true", "1"))
    ordinary = events.loc[~is_summary & ~events["event_id"].astype(str).isin(stats["event_id"].astype(str))].copy()
    included = details.loc[details["include_as_extra"].astype(str).str.lower().isin(("true","1"))].copy()
    parsed_ids = set(details["parent_event_id"].dropna().astype(str))
    unresolved = events.loc[is_summary & ~events["event_id"].astype(str).isin(parsed_ids)].copy()

    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_expanded_monthly import NO_NEW_EVENT_RE, summary_text, quiet_bucket
    quiet_mask = unresolved.apply(lambda r: bool(NO_NEW_EVENT_RE.search(summary_text(r))), axis=1)
    quiet = unresolved.loc[quiet_mask].copy()
    unresolved = unresolved.loc[~quiet_mask]

    datasets = []
    for source, frame, category, period_field in [
        ("vanlig", ordinary, "Händelse", ""),
        ("extra", included, "Händelse", "time"),
        ("oupplost", unresolved, "Händelse", ""),
        ("lugn", quiet, "Icke-händelse", "type_original")
    ]:
        part = valid_dates(frame)
        part["kind"] = category
        part["period"] = (part[period_field].map(block_from_time) if source == "extra"
                          else part[period_field].map(quiet_bucket) if source == "lugn"
                          else "")
        part.loc[~part["period"].isin(BLOCKS), "period"] = ""
        part["event_type"] = part["event_type_extracted"] if source == "extra" else (
            part["type_original"] if source == "vanlig" else
            "Sammanfattning, ej uppdelad" if source == "oupplost" else "Lugn sammanfattning"
        )
        datasets.append(part[["date", "geography_group", "kind", "period", "event_type"]])
    combined = pd.concat(datasets, ignore_index=True)
    combined["year"] = combined["date"].dt.year
    combined["weekday"] = combined["date"].dt.weekday
    combined["time_known"] = combined["period"].ne("").astype(int)
    combined["event_count"] = 1
    result = combined.groupby(
        ["year", "geography_group", "kind", "period", "event_type", "weekday", "time_known"],
        dropna=False
    )["event_count"].sum().reset_index()
    result.to_csv(OUT, index=False, encoding="utf-8")
    print(f"dated_observations={len(combined)} assigned_period={int(combined['time_known'].sum())}")

if __name__ == "__main__":
    main()
